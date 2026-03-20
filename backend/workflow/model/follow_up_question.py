from typing import List

from pydantic import BaseModel, Field


class FollowUpQuestion(BaseModel):
    questions: List[str] = Field(
        description=(
            "Exactly 5 follow-up suggestion strings rendered as quick-reply buttons. "
            "Must include hotel search, photos, things to do, travel time, and modify trip."
        )
    )

    def to_dict(self) -> dict:
        return {
            "follow_up_questions": self.follow_up_questions,
        }
