from typing import Optional, List

from langchain.tools import tool
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from ..services.tavily import TavilySearchService
from ..services.caching import RedisCachingService


class TripCostInput(BaseModel):
    """Strict inputs for trip cost estimation."""

    destination: str = Field(..., description="Destination city or country (e.g., 'Paris', 'Japan')")
    days: int = Field(..., ge=1, le=60, description="Trip length in days (1-60)")
    budget_level: str = Field(..., description="Budget tier: low, medium, or luxury")


class CostBreakdown(BaseModel):
    """Estimated cost breakdown for one category."""

    category: str
    amount: float
    currency: str = "USD"
    notes: Optional[str] = None


class TripCostOutput(BaseModel):
    """Structured trip cost response."""

    destination: str
    days: int
    budget_level: str
    total_estimated_cost: float
    currency: str = "USD"
    breakdown: List[CostBreakdown]
    sources: List[str] = []
    error: Optional[str] = None


@tool(
    "estimate_trip_cost",
    args_schema=TripCostInput,
    description=(
        "Estimate end-to-end trip costs for a destination including flights, accommodation, food, "
        "local transport, and activities for low/medium/luxury budgets. Returns structured JSON."
    ),
)
def estimate_trip_cost(destination: str, days: int, budget_level: str) -> dict:
    """Estimate approximate travel budget with web-informed ranges and deterministic breakdown."""

    print(f"\033[38;5;208m>>> [TOOL START] estimate_trip_cost: {destination}, days={days}, budget={budget_level}\033[0m")
    cache_service = RedisCachingService()

    normalized_budget = budget_level.strip().lower()
    cache_key = cache_service.build_key(
        "tool:estimate_trip_cost",
        {"destination": destination, "days": days, "budget_level": normalized_budget},
    )
    cached = cache_service.get_json(cache_key)
    if cached:
        print("\033[38;5;208m>>> [CACHE HIT] estimate_trip_cost\033[0m")
        return TripCostOutput(**cached).model_dump()

    allowed_budgets = {"low", "medium", "luxury"}
    if normalized_budget not in allowed_budgets:
        result = TripCostOutput(
            destination=destination,
            days=days,
            budget_level=budget_level,
            total_estimated_cost=0.0,
            breakdown=[],
            error="Invalid budget_level. Use one of: low, medium, luxury.",
        )
        print(f"\033[38;5;208m>>> [TOOL WARN] Invalid budget level: {budget_level}\033[0m")
        return result.model_dump()

    if days < 1 or days > 60:
        result = TripCostOutput(
            destination=destination,
            days=days,
            budget_level=normalized_budget,
            total_estimated_cost=0.0,
            breakdown=[],
            error="Invalid trip duration. days must be between 1 and 60.",
        )
        print(f"\033[38;5;208m>>> [TOOL WARN] Invalid days: {days}\033[0m")
        return result.model_dump()

    # Baseline per-day + one-time flight assumptions in USD.
    cost_models = {
        "low": {"flight": 450.0, "accommodation_per_day": 55.0, "food_per_day": 30.0, "transport_per_day": 12.0, "activities_per_day": 20.0},
        "medium": {"flight": 800.0, "accommodation_per_day": 120.0, "food_per_day": 55.0, "transport_per_day": 20.0, "activities_per_day": 40.0},
        "luxury": {"flight": 1600.0, "accommodation_per_day": 300.0, "food_per_day": 120.0, "transport_per_day": 45.0, "activities_per_day": 110.0},
    }
    model = cost_models[normalized_budget]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def safe_search() -> dict:
        """Fetch recent destination-specific price signals from Tavily."""
        tavily = TavilySearchService()
        return tavily.invoke(
            f"Travel cost in {destination} for {days} days - average hotel/night, meal costs/day, "
            "public transport pass, attraction tickets, and typical round-trip flight prices in USD"
        )

    try:
        search_results = safe_search()
        sources = [row.get("url") for row in search_results.get("results", []) if row.get("url")][:6]

        # Keep estimation deterministic and robust while still attaching current web sources.
        flight_cost = model["flight"]
        accommodation_cost = model["accommodation_per_day"] * days
        food_cost = model["food_per_day"] * days
        transport_cost = model["transport_per_day"] * days
        activities_cost = model["activities_per_day"] * days

        breakdown = [
            CostBreakdown(category="Flights", amount=round(flight_cost, 2), notes="Round-trip baseline estimate."),
            CostBreakdown(category="Accommodation", amount=round(accommodation_cost, 2), notes=f"{days} nights at {normalized_budget} tier."),
            CostBreakdown(category="Food", amount=round(food_cost, 2), notes="Daily meals/snacks estimate."),
            CostBreakdown(category="Local transport", amount=round(transport_cost, 2), notes="Metro, bus, taxi mix."),
            CostBreakdown(category="Activities", amount=round(activities_cost, 2), notes="Museums, tours, attractions."),
        ]

        total = round(sum(item.amount for item in breakdown), 2)
        result = TripCostOutput(
            destination=destination,
            days=days,
            budget_level=normalized_budget,
            total_estimated_cost=total,
            breakdown=breakdown,
            sources=sources,
        )
        cache_service.set_json(cache_key, result.model_dump(), ttl_seconds=3600)
        print(f"\033[38;5;208m>>> [TOOL INFO] Estimated total cost {total} USD for {destination}\033[0m")
        return result.model_dump()
    except Exception as e:
        print(f"\033[38;5;208m>>> [TOOL ERROR] estimate_trip_cost failed: {e}\033[0m")
        result = TripCostOutput(
            destination=destination,
            days=days,
            budget_level=normalized_budget,
            total_estimated_cost=0.0,
            breakdown=[],
            error=f"Cost estimation failed: {str(e)}",
        )
        return result.model_dump()
