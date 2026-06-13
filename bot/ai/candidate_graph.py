from langgraph.graph import StateGraph , END

from bot.ai.candidate_schemas import CandidateState, CandidateProfile

from bot.ai.candidate_agent import interviewer
from pydantic import ValidationError

async def analyzer(state: CandidateState):
    return await interviewer(state)

async def should_continue(state: CandidateState):
    if state.get("is_completed"):
        return "end"
    return "stop_and_wait"


workflow = StateGraph(CandidateState)
workflow.add_node("analyzer",analyzer)
workflow.set_entry_point("analyzer")

workflow.add_conditional_edges(
    "analyzer",
    should_continue,
    {
        "end": END,
        "stop_and_wait": END
    })

candidate_bot_app = workflow.compile()