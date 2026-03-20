from typing import Optional
from langgraph.graph import MessagesState

class AgentState(MessagesState):

    """
    budget: The budget for the trip
    source: The source of the trip
    destination: The destination of the trip
    travel_duration: The duration of the trip
    travel_date: The date of the trip

    These 5 required fields to be set before the trip can be planned.
    """

    budget: Optional[str]
    source: Optional[str]
    destination: Optional[str]
    travel_duration: Optional[int]
    travel_date: Optional[str]

    current_date_time: Optional[str]
    travel_timings: Optional[dict]
    transportation: Optional[dict]
    things_to_do: Optional[dict]
    travel_tips: Optional[dict]
    full_trip_plan: Optional[str]
    web_search_queries: Optional[list[str]]

    follow_up_questions: Optional[list[str]]

    ui_type: Optional[str]
    hotel_search_results: Optional[dict]

    cycle_count: Optional[int]
    input_guardrail_decision: Optional[str]
    output_guardrail_applied: Optional[bool]