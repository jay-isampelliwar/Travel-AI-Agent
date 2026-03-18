from pydantic import BaseModel, Field
from typing import Optional


class ChatMessage(BaseModel):
    ai_message: str = Field(description="Response the assistant should send to the user")

    source: Optional[str] = Field(
        default=None,
        description="Starting location mentioned by the user, if provided",
    )
    destination: Optional[str] = Field(
        default=None,
        description="Destination location mentioned by the user, if provided",
    )
    travel_duration: Optional[int] = Field(
        default=None,
        description="Duration of the journey travelers can choose",
    )
    travel_date: Optional[str] = Field(
        default=None,
        description="Date of the journey travelers can choose",
    )

