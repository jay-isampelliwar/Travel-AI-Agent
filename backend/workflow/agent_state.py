from typing import Optional
from langgraph.graph import MessagesState

class AgentState(MessagesState):
    travel_timings: Optional[dict]
    transportation: Optional[dict]
    things_to_do: Optional[dict]
    travel_tips: Optional[dict]
    source: Optional[str]
    destination: Optional[str]
    travel_duration: Optional[int]
    travel_date: Optional[str]
    full_trip_plan: Optional[str]
    query: Optional[str]