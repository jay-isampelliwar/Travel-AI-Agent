from typing import Any, Dict, List

from pydantic import BaseModel


class AgentRequest(BaseModel):
    user_message: str
    user_id: str
    thread_id: str
    session_id: str


class AgentResponse(BaseModel):
    message: str
    ui_type: str = "None"
    data: Dict[str, Any]
    follow_up_questions: List[str]
