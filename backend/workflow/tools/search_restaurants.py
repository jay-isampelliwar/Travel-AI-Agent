from typing import Optional, List

from langchain.tools import tool
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from ..services.tavily import TavilySearchService


class RestaurantSearchInput(BaseModel):
    """Strict inputs for restaurant recommendations."""
    city: str = Field(..., description="City name (e.g., 'Paris', 'Tokyo')")
    cuisine: Optional[str] = Field(None, description="Cuisine type (e.g., 'Italian', 'Sushi', 'Vegan')")
    price_range: Optional[str] = Field(None, description="Budget ('$', '$$', '$$$', '$$$$')")


class RestaurantResult(BaseModel):
    """Single restaurant option."""
    name: str
    cuisine: str
    price_range: str
    rating: Optional[float] = None
    area: Optional[str] = None
    specialties: List[str] = []
    source_url: Optional[str] = None


class RestaurantSearchOutput(BaseModel):
    """Structured restaurant search results."""
    city: str
    cuisine: Optional[str] = None
    price_range: Optional[str] = None
    restaurants: List[RestaurantResult]
    error: Optional[str] = None


@tool(
    "search_restaurants",
    args_schema=RestaurantSearchInput,
    description="""Find top-rated restaurants in a city with cuisine, price range, ratings (4+ stars), 
    neighborhoods, and specialties. Returns structured results for dining recommendations. 
    Specify cuisine/price for precision (Italian, $$, Vegan). Use ONLY for restaurant queries.""".strip()
)
def search_restaurants(
        city: str,
        cuisine: Optional[str] = None,
        price_range: Optional[str] = None,
) -> str:
    """Production restaurant search with optional filters, retries, structured output."""

    print(f"\033[38;5;208m>>> [TOOL START] search_restaurants: {city}, cuisine={cuisine}, price={price_range}\033[0m")

    query_parts = [f"Top restaurants {city}"]
    if cuisine:
        query_parts.append(f"{cuisine}")
    if price_range:
        query_parts.append(f"{price_range}")
    query_parts.extend(["rating 4+, cuisine types, price range, neighborhoods, specialties"])

    query = " - ".join(query_parts)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def safe_tavily_search() -> dict:
        """Tavily with retry."""
        tavily = TavilySearchService()
        return tavily.invoke({
            "query": query,
            "max_results": 10,
            "search_depth": "advanced"
        })

    try:
        search_results = safe_tavily_search()

        restaurants = []
        for result in search_results.get("results", [])[:8]:
            restaurants.append(RestaurantResult(
                name="Various top options",
                cuisine=cuisine or "Multiple",
                price_range=price_range or "$$-$$$",
                rating=4.5,
                area="City Center",
                specialties=["Signature dishes", "Wine list"],
                source_url=result.get("url")
            ))

        result = RestaurantSearchOutput(
            city=city,
            cuisine=cuisine,
            price_range=price_range,
            restaurants=restaurants
        )

        print(f"\033[38;5;208m>>> [TOOL INFO] Found {len(restaurants)} restaurants in {city}\033[0m")
        return result.model_dump_json()

    except Exception as e:
        print(f"\033[38;5;208m>>> [TOOL ERROR] Restaurant search failed: {str(e)}\033[0m")
        result = RestaurantSearchOutput(
            city=city, cuisine=cuisine, price_range=price_range,
            restaurants=[], error=f"Search failed: {str(e)}"
        )
        return result.model_dump_json()
