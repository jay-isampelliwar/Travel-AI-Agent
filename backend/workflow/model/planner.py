from typing import List

from pydantic import BaseModel, Field


class Planner(BaseModel):
    summary: str = Field(
        description=(
            "The complete trip plan in markdown format. "
            "Must contain ALL five sections in order: "
            "Trip Overview, How to Get There, Timing & Seasonal Advice, "
            "Essential Travel Tips, and Quick Reference Summary. "
            "Never truncate. Never skip a section."
        )
    )
    follow_up_questions: List[str] = Field(
        description=(
            "Exactly 5 follow-up suggestion strings rendered as quick-reply buttons. "
            "Must include hotel search, photos, things to do, travel time, and modify trip."
        )
    )

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "follow_up_questions": self.follow_up_questions,
        }
