from pydantic import BaseModel, Field
from typing import List


class TravelTip(BaseModel):
    title: str = Field(description="Short title of the travel tip")
    advice: str = Field(description="Explanation or recommendation for the traveler")

    def to_dict(self):
        return {
            "title": self.title,
            "advice": self.advice,
        }


class TravelTips(BaseModel):
    tips: List[TravelTip] = Field(description="Helpful travel tips for visitors")

    def to_dict(self):
        return {
            "tips": [tip.to_dict() for tip in self.tips],
        }

