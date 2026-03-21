from typing import Optional
from langgraph.graph import MessagesState

class AgentState(MessagesState):
    current_date_time: Optional[str]
    follow_up_questions: Optional[list[str]]
    ui_type: Optional[str]
    hotel_search_results: Optional[dict]
    cycle_count: Optional[int]
    input_guardrail_decision: Optional[str]
    output_guardrail_applied: Optional[bool]

    last_tool_call: Optional[str]