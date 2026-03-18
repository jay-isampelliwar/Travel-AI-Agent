from pydantic import BaseModel, Field
from typing import List


class ResultItem(BaseModel):
    name: str = Field(
        description="Name of the hotel or restaurant"
    )
    url: str = Field(
        description="Direct link to the hotel or restaurant page"
    )
    price: float = Field(
        description="Approximate price per night or average meal cost in the local currency"
    )
    description: str = Field(
        description="Short summary of what makes this place suitable for travelers"
    )
    rating: float = Field(
        description="Average traveler rating (for example, from 1.0 to 5.0)"
    )


class HotelRestaurantSearch(BaseModel):
    list_of_results: List[ResultItem] = Field(
        description="List of recommended hotels or restaurants that match the search"
    )

    def to_dict(self):
        return {
            "results": [
                {
                    "name": item.name,
                    "url": item.url,
                    "price": item.price,
                    "description": item.description,
                    "rating": item.rating,
                }
                for item in self.list_of_results
            ]
        }
