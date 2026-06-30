import os
from langchain_openai import ChatOpenAI
from bot.ai.candidate_schemas import CandidateState, CandidateProfile, ScreeningResponse, CandidateVerdict, CandidateSearchQueryParsed
from langchain_core.messages import SystemMessage
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

import sys
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from bot.utils.utils import clear_github_username

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3,
    api_key=os.getenv("OPENAI_API_KEY")
)

def convert_mcp_to_openai(mcp_tools) -> list:
    """Converts tools from the MCP format to the OpenAI Function Calling format."""
    openai_tools = []
    for tool in mcp_tools.tools:
        openai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
        )
    return openai_tools

async def analyze_query_vacancies(query: str):

    analyze_query_llm = llm.with_structured_output(CandidateSearchQueryParsed)

    system_prompt = f"""
    You are an intelligent assistant for a recruitment platform. Your task is to analyze an incoming job search query from a user and break it down into two main components:
    1. A semantic search string search_phrase, which will later be used to generate a vector embedding.
    2. Structured filters (filters) for precise querying in an SQL database.

    DATA EXTRACTION RULES:
    1. `search_phrase`: Remove all conversational filler (e.g., "hello", "I'm looking for a job", "preferably"). Keep only the job title and core technologies. Append 2-3 popular synonyms separated by spaces (for example, if the query mentions "frontend", add "frontend react UI engineer"). Do not include location or salary expectations here.
    2. `work_mode`: Look for key phrases. "From home", "remote", "remotely" -> 'Remote'. "In office", "locally", "on-site" -> 'Office'. If not mentioned, set to null.
    3. `work_location`: Extract the city or country if specified. If not mentioned, set to null.
    4. `salary_expectations`: If the user says "from $2000", record 2000. If they say "around $3000", record 2500 (leave a small downward margin so as not to miss relevant opportunities).
    5. `experience_years`: If the candidate writes "I'm a junior with 1 year of experience", record 1.
    6. `skills`: Strictly extract programming languages, frameworks, and tools (e.g., 'PostgreSQL', 'Docker', 'Python'). Be conservative — do not hallucinate or invent technologies that are not explicitly present in the text.

    CRITICAL REQUIREMENT: Return the response strictly in JSON format according to the provided JSON schema. Do not add any introductory text, pleasantries, or explanations.
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]

    result = await analyze_query_llm.ainvoke(messages)
    print(result)
    return result

async def interviewer(state: CandidateState):
    structured_llm = llm.with_structured_output(ScreeningResponse)
    
    current_cand = state.get("candidate", {}) or {}
    already_asked = state.get("asked_skills", []) or []

    required_skills = state.get('vacancy_data', {}).get('required_skills', [])

    system_prompt = f"""You are an AI Recruiter. Your task is to conduct a short, efficient screening interview.

    🔴 LANGUAGE REQUIREMENT:
    - The entire interview MUST be conducted STRICTLY in English. 
    - Formulate the `next_question` ONLY in English.

    VACANCY INFORMATION:
    {state.get('vacancy_data')}

    MANDATORY HARD SKILLS FROM JOB DESCRIPTION:
    {', '.join(required_skills) if required_skills else 'No specific hard skills listed'}

    CURRENT CANDIDATE PROFILE (ALREADY COLLECTED DATA):
    - Location: {current_cand.get('location') or '❌ not collected'}
    - Work Mode: {current_cand.get('work_mode') or '❌ not collected'} 
    - Experience (years): {current_cand.get('experience') or '❌ not collected'}
    - Skills (Confirmed): {', '.join(current_cand.get('skills', [])) if current_cand.get('skills') else '❌ not collected'}
    - GitHub: {current_cand.get('github') or '❌ not collected'}
    - Project Experience Saved: {"Yes" if current_cand.get('project_experience') else "❌ not collected"}

    🚫 TECHNOLOGIES ALREADY ASKED ABOUT (NEVER ASK ABOUT THEM AGAIN):
    {', '.join(already_asked) if already_asked else 'Nothing asked yet'}

    PROFILE UPDATE & BEHAVIOR RULES:
    - If the candidate responds "yes"/"ready"/"generally yes" to a hybrid work question → work_mode = "hybrid"
    - If "no"/"not ready" to hybrid → work_mode = "office" or "remote" (clarify with the next question)
    - If the candidate responds "yes" to an office question → work_mode = "office"  
    - If the candidate responds "yes" to a remote question → work_mode = "remote"
    - IMPORTANT: Any valid answer to the work_mode question = RECORD the value and DO NOT ask about it again.
    
    ⚠️ MANDATORY GITHUB RULES:
    - Asking for a GitHub profile link is MANDATORY.
    - If the candidate provides a link or username → record the exact value to the `github` field.
    - If the candidate states in ANY form that they do not have GitHub (e.g., "no", "don't use", "I don't have it") → you MUST record the exact string "None" to the `github` field.
    - Once the `github` field contains a link OR "None", it is considered FULLY COLLECTED.

    ⚠️ SKILLS & PROJECTS INTERVIEW PROTOCOL:
    Instead of asking about each mandatory technology individually, you must follow these steps for core skills and experience:

    1. THE BULK SKILLS QUESTION (Do not ask individual questions for core skills!):
       - If mandatory skills haven't been checked yet, ask EXACTLY ONE question formatted strictly in English like this: "Which of the core skills do you have experience with? ({', '.join(required_skills)})"
       - The candidate is expected to reply with a list of technologies.
       - Analyze their response and add ALL technologies they confirmed into the `skills` list in the profile.
       - Mark all listed required skills as checked/asked by logging them in your internal response logic.

    2. THE PROJECT EXPERIENCE QUESTION (Instead of deep-diving into tech details):
       - Ask EXACTLY ONE question requesting the candidate to describe one or multiple of their projects and what those projects do.
       - Do not ask separate questions for descriptions of each technology. Get the project story in one go.
       - Extract information about their project experience and save it to the `project_experience` field to mark this stage as done.

    3. STAGE 2: Additional Skills (Nice to Have)
       - Ask about these remaining skills one by one, EXACTLY ONCE, only after the core skills and project questions are completed.
       - If the candidate responds AFFIRMATIVELY → add to `skills`. If NEGATIVELY → DO NOT add it.
       - Always record the name of the tech in the `just_asked_skill` field.

    INSTRUCTIONS:
    1. Analyze the dialogue history and the candidate's latest message. Update fields in `candidate_profile`.
    2. Check what information is still missing. You MUST explicitly ask about every single field from the CURRENT CANDIDATE PROFILE that is marked as '❌ not collected' (Location, Work Mode, Experience, GitHub, Core Skills, and Project Experience).
    3. Prioritize missing fields: General fields (Location, Work Mode, Experience) & GitHub -> Bulk Skills Question -> Project Experience Question -> Nice to Have skills one by one.
    4. Formulate EXACTLY ONE specific next question in the `next_question` field in English. Never pack multiple questions from different stages into one message!
    5. ONLY when all fields (Location, Work Mode, Experience, GitHub, Core Skills, Project Experience) have been fully collected and nice-to-have skills have been queried — set `is_completed: true`."""

    messages_for_llm = [SystemMessage(content=system_prompt)] + state["messages"]
    
    response: ScreeningResponse = await structured_llm.ainvoke(messages_for_llm)
    
    new_asked_skills = list(already_asked)
    if response.just_asked_skill:
        new_asked_skills.append(response.just_asked_skill)
    
    ai_message = AIMessage(content=response.next_question)
    
    return {
        "candidate": response.candidate_profile.model_dump(),
        "next_question": response.next_question,
        "is_completed": response.is_completed,
        "asked_skills": new_asked_skills,
        "messages": [ai_message] 
    }

async def analyze_interviewer(vacancy_data: dict, candidate_profile: dict):
    analyzer_llm = llm.with_structured_output(CandidateVerdict)

    ### Get the user's last 3 repositories from GitHub
    github_value = candidate_profile.get("git_hub_url")

    github__clear_value = await clear_github_username(github_value)
    print(github__clear_value)
    github_analysis_text = "No GitHub data available or analyzed."

    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, "mcp-server", "server.py")
    if github__clear_value and github__clear_value != "None":
        server_params = StdioServerParameters(
            command=sys.executable,  
            args=[server_path],      
            env=None
        )
        try:
            print(f"[MCP] Starting a server for analyzing a developer's GitHub: {github__clear_value}")
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as mcp_session:
                    await mcp_session.initialize()
                    
                    mcp_result = await mcp_session.call_tool(
                        "analyze_user_repos", 
                        arguments={"username": github__clear_value}
                    )
                    github_analysis_text = mcp_result.content[0].text
                    print("[MCP] GitHub has been successfully analyzed!")
                    
        except Exception as e:
            github_analysis_text = f"Failed to analyze GitHub due to server error: {str(e)}"
            print(f"[MCP Error] {github_analysis_text}")
    ###

    system_prompt = f"""You are an expert IT Technical Recruiter and Talent Acquisition Specialist.
    Your task is to objectively evaluate a candidate's profile against the job vacancy requirements.

    VACANCY REQUIREMENTS:
    {vacancy_data}

    CANDIDATE PROFILE:
    {candidate_profile}

    GITHUB ANALYSIS DATA:
    {github_analysis_text}

    EVALUATION GUIDELINES:
    1. match_percentage: Calculate logically. Full match of core skills and experience = 90-100%. Missing core skills should drop this significantly.
    2. verdict: Set "Hire" if match_percentage >= 70% and there are no critical blockers, otherwise "No Hire".
    3. matched_skills & missing_skills: Compare the 'skills' and 'nice_to_have' fields from the vacancy with the candidate's 'skills'.
    4. pros & cons: Evaluate 'experience', 'work_mode' alignment, 'location', and 'git_hub_url'.
    5. github_summary: Analyze the "GITHUB ANALYSIS DATA" provided above. 
    - If the text contains the word "failed" or is empty/missing, set this field to "No GitHub data provided".
    - Otherwise, provide a concise technical review of the candidate's real GitHub projects based on that data.
    6. summary: Provide a 2–3 sentence synthesis of why this verdict and percentage were chosen.

    OUTPUT REQUIREMENTS:
    - You must strictly fulfill the schema constraints.
    - The text fields (`summary`, `pros`, `cons`) must be written in English.
    - Technical skill names must remain in English as specified in the data.
    """

    return await analyzer_llm.ainvoke(system_prompt)
