from langchain.tools import tool


@tool(
    "generate_itinerary",
    description="Generate a day-by-day travel itinerary for a destination based on trip duration and traveler interests."
)
def generate_itinerary(destination: str, days: int, interests: list[str]) -> str:
    """Generate a day-by-day travel itinerary including attractions, activities, restaurants, and sightseeing."""
    pass
