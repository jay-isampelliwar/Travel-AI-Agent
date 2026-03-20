from typing import List
from pydantic import BaseModel, Field


class FollowUpSuggestions(BaseModel):
    suggestions: List[str] = Field(
        description=(
            "Exactly 5 short quick-reply suggestions rendered as buttons. "
            "Each suggestion is a natural traveler response to the assistant's last message."
        )
    )

    def to_dict(self) -> dict:
        return {
            "suggestions": self.suggestions,
        }