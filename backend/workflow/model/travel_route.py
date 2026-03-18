from pydantic import BaseModel, Field
from typing import List


class TransportOption(BaseModel):
    transport_type: str = Field(description="Type of transport used for the journey")
    travel_time: str = Field(description="Approximate travel duration")
    route_description: str = Field(description="Short explanation of how the journey works")
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
    start_location: str = Field(description="City where the journey begins")
    destination: str = Field(description="Final destination of the journey")
    transport_options: List[TransportOption] = Field(
        description="Available transport methods travelers can choose"
    )

    def to_dict(self):
        return {
            "start_location": self.start_location,
            "destination": self.destination,
            "transport_options": [option.to_dict() for option in self.transport_options],
        }

