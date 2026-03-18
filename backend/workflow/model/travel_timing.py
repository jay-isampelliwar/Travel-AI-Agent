from pydantic import BaseModel, Field
from typing import List


class TravelTiming(BaseModel):
    best_time_to_visit: str = Field(description="Best months or season to visit the destination")
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

