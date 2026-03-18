from pydantic import BaseModel, Field
from typing import List


class Activity(BaseModel):
    activity_name: str = Field(description="Main activity travelers can do")
    description: str = Field(description="Short explanation of the activity")

    def to_dict(self):
        return {
            "activity_name": self.activity_name,
            "description": self.description,
        }


class ThingsToDo(BaseModel):
    destination: str = Field(description="Travel destination name")
    activities: List[Activity] = Field(description="Top activities travelers can do")

    def to_dict(self):
        return {
            "destination": self.destination,
            "activities": [activity.to_dict() for activity in self.activities],
        }

