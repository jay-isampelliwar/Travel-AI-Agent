from typing import Optional
from langgraph.graph import MessagesState

class AgentState(MessagesState):
    current_date_time: Optional[str]
    travel_timings: Optional[dict]
    transportation: Optional[dict]
    things_to_do: Optional[dict]
    travel_tips: Optional[dict]
    source: Optional[str]
    destination: Optional[str]
    travel_duration: Optional[int]
    travel_date: Optional[str]
    full_trip_plan: Optional[str]
    web_search_queries: Optional[list[str]]