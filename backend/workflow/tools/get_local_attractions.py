from typing import List, Optional

from langchain.tools import tool
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from ..services.tavily import TavilySearchService
from ..services.caching import RedisCachingService


class LocalAttractionsInput(BaseModel):
    """Strict input for attraction discovery."""

    destination: str = Field(..., description="City or region name, e.g. 'Rome'")


class AttractionItem(BaseModel):
    """Single attraction suggestion."""

    name: str
    category: str
    brief: str
    source_url: Optional[str] = None


class LocalAttractionsOutput(BaseModel):
    """Structured attraction response."""

    destination: str
    attractions: List[AttractionItem]
    error: Optional[str] = None


@tool(
    "get_local_attractions",
    args_schema=LocalAttractionsInput,
    description=(
        "Retrieve popular attractions and things to do in a destination including "
        "landmarks, museums, neighborhoods, parks, and markets. Returns structured JSON."
    ),
)
def get_local_attractions(destination: str) -> str:
    """Discover local attractions with structured output."""

    print(f"\033[38;5;208m>>> [TOOL START] get_local_attractions: {destination}\033[0m")
    cache_service = RedisCachingService()
    cache_key = cache_service.build_key(
        "tool:get_local_attractions",
        {"destination": destination},
    )
    cached = cache_service.get_json(cache_key)
    if cached:
        print("\033[38;5;208m>>> [CACHE HIT] get_local_attractions\033[0m")
        return LocalAttractionsOutput(**cached).model_dump_json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=3, max=10))
    def safe_search() -> dict:
        tavily = TavilySearchService()
        return tavily.invoke(
            f"Top attractions in {destination} including landmarks, museums, parks, local markets, neighborhoods, and unique things to do"
        )

    try:
        search_results = safe_search()
        items: List[AttractionItem] = []
        categories = ["landmark", "museum/culture", "nature/park", "local experience"]

        for idx, row in enumerate(search_results.get("results", [])[:8]):
            items.append(
                AttractionItem(
                    name=row.get("title", "Popular local attraction"),
                    category=categories[idx % len(categories)],
                    brief="Highly rated and frequently recommended for first-time visitors.",
                    source_url=row.get("url"),
                )
            )

        result = LocalAttractionsOutput(destination=destination, attractions=items)
        cache_service.set_json(cache_key, result.model_dump(), ttl_seconds=3600)
        print(
            f"\033[38;5;208m>>> [TOOL INFO] Found {len(items)} attraction sources for {destination}\033[0m"
        )
        return result.model_dump_json()
    except Exception as e:
        print(f"\033[38;5;208m>>> [TOOL ERROR] attractions search failed: {e}\033[0m")
        result = LocalAttractionsOutput(
            destination=destination,
            attractions=[],
            error=f"Attraction lookup failed: {str(e)}",
        )
        return result.model_dump_json()
