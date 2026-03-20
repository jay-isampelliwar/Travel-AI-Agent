from langchain.tools import tool


@tool(
    "estimate_trip_cost",
    description="Estimate total trip cost including flights, accommodation, food, transport, and activities based on budget level."
)
def estimate_trip_cost(destination: str, days: int, budget_level: str) -> str:
    """Estimate approximate travel budget. budget_level: 'low', 'medium', or 'luxury'."""
    pass
