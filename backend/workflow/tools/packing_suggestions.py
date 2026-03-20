from typing import List

from langchain.tools import tool
from pydantic import BaseModel, Field


class PackingInput(BaseModel):
    """Strict packing inputs."""

    destination: str = Field(..., description="Destination city/country")
    days: int = Field(..., ge=1, le=60, description="Trip duration in days")
    weather: str = Field(..., description="Expected weather summary, e.g. 'rainy 10-15C'")


class PackingOutput(BaseModel):
    """Structured packing suggestions."""

    destination: str
    days: int
    weather: str
    clothing: List[str]
    essentials: List[str]
    documents: List[str]
    electronics: List[str]
    health_and_comfort: List[str]


@tool(
    "packing_suggestions",
    args_schema=PackingInput,
    description=(
        "Suggest practical packing checklist based on destination, trip duration, and weather. "
        "Returns structured lists for clothing, essentials, documents, electronics, and comfort."
    ),
)
def packing_suggestions(destination: str, days: int, weather: str) -> str:
    """Generate a packing checklist as JSON."""

    print(
        f"\033[38;5;208m>>> [TOOL START] packing_suggestions: {destination}, {days} days, weather={weather}\033[0m"
    )

    weather_l = weather.lower()
    clothing = ["Comfortable walking shoes", "Everyday outfits", "Sleepwear", "Undergarments", "Socks"]

    if "rain" in weather_l or "shower" in weather_l:
        clothing.extend(["Waterproof jacket", "Compact umbrella", "Quick-dry layers"])
    if "cold" in weather_l or "snow" in weather_l or "0" in weather_l or "-1" in weather_l:
        clothing.extend(["Thermal base layers", "Warm coat", "Beanie and gloves"])
    if "hot" in weather_l or "sunny" in weather_l or "30" in weather_l:
        clothing.extend(["Breathable shirts", "Sun hat", "Lightweight shorts/trousers"])

    result = PackingOutput(
        destination=destination,
        days=days,
        weather=weather,
        clothing=clothing,
        essentials=[
            "Toiletries kit (travel-size)",
            "Reusable water bottle",
            "Day bag",
            "Laundry pouch",
            "Travel locks",
        ],
        documents=[
            "Passport and copies",
            "Visa / entry documents (if applicable)",
            "Travel insurance",
            "Flight and accommodation confirmations",
            "Emergency contacts and local address",
        ],
        electronics=[
            "Phone + charger",
            "Power bank",
            "Universal travel adapter",
            "Earphones",
            "Camera (optional)",
        ],
        health_and_comfort=[
            "Personal medications",
            "Basic first-aid items",
            "Sunscreen",
            "Hand sanitizer/wipes",
            "Neck pillow/eye mask for transit",
        ],
    )

    print(f"\033[38;5;208m>>> [TOOL INFO] Packing list generated for {destination}\033[0m")
    return result.model_dump_json()
