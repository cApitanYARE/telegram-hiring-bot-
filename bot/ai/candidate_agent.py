import os
from langchain_openai import ChatOpenAI
from bot.ai.candidate_schemas import CandidateState, CandidateProfile, ScreeningResponse
from langchain_core.messages import SystemMessage
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3,
    api_key=os.getenv("OPENAI_API_KEY")
)

async def interviewer(state: CandidateState):
    structured_llm = llm.with_structured_output(ScreeningResponse)
    
    current_cand = state.get("candidate", {}) or {}
    already_asked = state.get("asked_skills", []) or []

    system_prompt = f"""You are an AI Recruiter. Your task is to conduct a short screening interview.

    VACANCY INFORMATION:
    {state.get('vacancy_data')}

    CURRENT CANDIDATE PROFILE:
    - Location: {current_cand.get('location') or '❌ not collected'}
    - Work Mode: {current_cand.get('work_mode') or '❌ not collected'} 
    - Experience (years): {current_cand.get('experience') or '❌ not collected'}
    - Skills: {', '.join(current_cand.get('skills', [])) if current_cand.get('skills') else '❌ not collected'}
    - GitHub: {current_cand.get('github') or '❌ not collected'}

    🚫 TECHNOLOGIES ALREADY ASKED ABOUT (NEVER ASK ABOUT THEM AGAIN):
    {', '.join(already_asked) if already_asked else 'Nothing asked yet'}

    PROFILE UPDATE & BEHAVIOR RULES:
    - If the candidate responds "yes"/"ready"/"generally yes" to a hybrid work question → work_mode = "hybrid"
    - If "no"/"not ready" to hybrid → work_mode = "office" or "remote" (clarify with the next question)
    - If the candidate responds "yes" to an office question → work_mode = "office"  
    - If the candidate responds "yes" to a remote question → work_mode = "remote"
    - IMPORTANT: Any valid answer to the work_mode question = RECORD the value and DO NOT ask about it again.
    - If GitHub contains a link — the field is filled, DO NOT ask about it again.

    ⚠️ RULES FOR ADDITIONAL SKILLS (Nice to have):
    The job description includes nice-to-have requirements (TypeScript, TailwindCSS/Bootstrap, Figma). Your task is to ask the candidate about them one by one, EXACTLY ONCE:
    1. If the candidate responds AFFIRMATIVELY (e.g., "yes", "have experience", "learned it") → You MUST add this skill to the `skills` list of the current profile.
    2. If the candidate responds NEGATIVELY in any form (e.g., "no", "don't know", "haven't worked with it") → DO NOT add it to `skills`. 
    3. Make sure to specify the exact name of the technology you just checked in this step in the `just_asked_skill` field (values must be: 'TypeScript', 'TailwindCSS/Bootstrap', or 'Figma').

    INSTRUCTIONS:
    1. Analyze the dialogue history and the candidate's latest message. Update the corresponding fields in `candidate_profile`.
    2. Check the "🚫 TECHNOLOGIES ALREADY ASKED ABOUT" list. Determine which "Nice to have" technologies or mandatory fields you have NOT asked about yet.
    3. Formulate EXACTLY ONE specific next question in the `next_question` field. Ask STRICTLY about something that has not been covered yet!
    4. If all mandatory fields have been covered and the "Nice to have" block has been fully queried (regardless of yes/no answers) — set `is_completed: true`."""
    
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