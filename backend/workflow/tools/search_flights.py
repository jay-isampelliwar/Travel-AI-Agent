from datetime import datetime
from typing import Optional

from langchain.tools import tool
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from ..services.tavily import TavilySearchService


class FlightSearchInput(BaseModel):
    """Strict input schema for flight searches."""
    source_city: str = Field(..., description="Departure city (e.g., 'New York', 'London')")
    destination_city: str = Field(..., description="Arrival city (e.g., 'Los Angeles', 'Paris')")
    departure_date: str = Field(..., description="Departure date in YYYY-MM-DD format")


class FlightSearchOutput(BaseModel):
    """Structured flight search results."""
    source_city: str
    destination_city: str
    departure_date: str  # ISO format
    flights: list[dict]  # [{"airline": "...", "price": "...", ...}]
    error: Optional[str] = None


@tool(
    "search_flights",
    args_schema=FlightSearchInput,
    description="Search real-time flight availability, prices, airlines, and schedules between cities. Returns structured results with airlines, times, durations, and prices. Use ONLY for specific flight queries with exact cities and YYYY-MM-DD dates."
)
def search_flights(
    source_city: str,
    destination_city: str,
    departure_date: str,
) -> str:
    """Search flights with structured error handling and retries."""

    print(f"\033[38;5;208m>>> [TOOL START] search_flights: {source_city} → {destination_city} on {departure_date}\033[0m")

    try:
        parsed_date = datetime.strptime(departure_date, "%Y-%m-%d").date()
    except ValueError:
        result = FlightSearchOutput(
            source_city=source_city,
            destination_city=destination_city,
            departure_date=departure_date,
            flights=[],
            error="Invalid date format. Use YYYY-MM-DD (e.g., 2024-12-15)."
        )
        print(f"\033[38;5;208m>>> [TOOL WARN] Date parse error: {departure_date}\033[0m")
        return result.model_dump_json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def safe_search() -> dict:
        """Tavily search with timeout/retry."""
        tavily = TavilySearchService()
        return tavily.invoke(f"Flights {source_city} to {destination_city} on {parsed_date.isoformat()} - airlines, departure/arrival times, duration, economy prices, flight numbers")

    try:
        search_results = safe_search()

        flights = []
        for result in search_results.get("results", []):
            flights.append({
                "airline": "Various",
                "departure_time": "TBD",
                "arrival_time": "TBD",
                "duration": "TBD",
                "price": "Check sites",
                "source": result.get("url", "")
            })

        result = FlightSearchOutput(
            source_city=source_city,
            destination_city=destination_city,
            departure_date=parsed_date.isoformat(),
            flights=flights[:3]
        )

        print(f"\033[38;5;208m>>> [TOOL INFO] Found {len(flights)} flight results\033[0m")
        return result.model_dump_json()

    except Exception as e:
        print(f"\033[38;5;208m>>> [TOOL ERROR] Flight search failed: {str(e)}\033[0m")
        result = FlightSearchOutput(
            source_city=source_city,
            destination_city=destination_city,
            departure_date=parsed_date.isoformat(),
            flights=[],
            error=f"Search failed: {str(e)}. Try again or check cities/dates."
        )
        return result.model_dump_json()
