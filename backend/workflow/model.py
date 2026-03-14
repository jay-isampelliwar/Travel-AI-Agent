from pydantic import BaseModel, Field
from typing import List, Optional


class ChatMessage(BaseModel):
    ai_message: str = Field(
        description="Response the assistant should send to the user"
    )

    source: Optional[str] = Field(
        default=None,
        description="Starting location mentioned by the user, if provided"
    )

    destination: Optional[str] = Field(
        default=None,
        description="Destination location mentioned by the user, if provided"
    )

    travel_duration: Optional[int] = Field(
        default=None,
        description="Duration of the journey travelers can choose"
    )

    travel_date: Optional[str] = Field(
        default=None,
        description="Date of the journey travelers can choose"
    )

class TravelTiming(BaseModel):
    best_time_to_visit: str = Field(
        description="Best months or season to visit the destination"
    )

    peak_season_benefits: List[str] = Field(
        description="Key experiences travelers get during the best season"
    )

    missed_benefits_off_season: List[str] = Field(
        description="Experiences travelers will miss if visiting outside the best season"
    )

    off_season_benefits: List[str] = Field(
        description="Additional advantages travelers may get if visiting during the off-season"
    )

    def to_dict(self):
        return {
            "best_time_to_visit": self.best_time_to_visit,
            "peak_season_benefits": self.peak_season_benefits,
            "off_season_benefits": self.off_season_benefits,
            "missed_benefits": self.missed_benefits_off_season,
        }


class TransportOption(BaseModel):
    transport_type: str = Field(
        description="Type of transport used for the journey"
    )

    travel_time: str = Field(
        description="Approximate travel duration"
    )

    route_description: str = Field(
        description="Short explanation of how the journey works"
    )

    key_features: List[str] = Field(
        description="Comfort, convenience, or special features of this transport option"
    )

    def to_dict(self):
        return {
            "transport_type": self.transport_type,
            "travel_time": self.travel_time,
            "route_description": self.route_description,
            "key_features": self.key_features,
        }


class TravelRoute(BaseModel):
    start_location: str = Field(
        description="City where the journey begins"
    )

    destination: str = Field(
        description="Final destination of the journey"
    )

    transport_options: List[TransportOption] = Field(
        description="Available transport methods travelers can choose"
    )

    def to_dict(self):
        return {
            "start_location": self.start_location,
            "destination": self.destination,
            "transport_options": [
                option.to_dict() for option in self.transport_options
            ],
        }


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