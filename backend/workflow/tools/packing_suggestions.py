from langchain.tools import tool


@tool(
    "packing_suggestions",
    description="Suggest packing items for a trip based on destination, duration, and expected weather conditions."
)
def packing_suggestions(destination: str, days: int, weather: str) -> str:
    """Recommend clothing, travel accessories, documents, electronics, and essentials for the trip."""
    pass
