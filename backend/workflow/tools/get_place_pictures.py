from typing import List, Optional

from langchain.tools import tool
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from ..services.tavily import TavilySearchService


class PlacePicturesInput(BaseModel):
    """Input schema for place image lookup."""

    place_name: str = Field(..., description="Place or landmark name, e.g. 'Eiffel Tower'")
    city: Optional[str] = Field(None, description="Optional city for disambiguation")


class PlacePicturesOutput(BaseModel):
    """Structured output for image URL retrieval."""

    place_name: str
    city: Optional[str] = None
    image_urls: List[str]
    source_urls: List[str]
    error: Optional[str] = None


@tool(
    "get_place_pictures",
    args_schema=PlacePicturesInput,
    description=(
        "Retrieve representative image URLs for a place or landmark. "
        "Returns a list of direct-looking image URLs that can be appended to LLM context."
    ),
)
def get_place_pictures(place_name: str, city: Optional[str] = None) -> str:
    """Return a list of image URLs for a place."""

    query_target = f"{place_name}, {city}" if city else place_name
    print(f"\033[38;5;208m>>> [TOOL START] get_place_pictures: {query_target}\033[0m")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=3, max=10))
    def safe_search() -> dict:
        tavily = TavilySearchService()
        return tavily.invoke(
            {
                "query": (
                    f"{query_target} high quality photos images official tourism media kit "
                    "Wikimedia Unsplash Pexels"
                ),
                "max_results": 12,
                "search_depth": "advanced",
            }
        )

    def _extract_image_urls(results: List[dict]) -> List[str]:
        image_urls: List[str] = []
        keys = ("image", "image_url", "thumbnail", "thumbnail_url")
        for row in results:
            for key in keys:
                val = row.get(key)
                if isinstance(val, str) and val.startswith("http"):
                    image_urls.append(val)
        # De-duplicate and keep only common image extensions when possible
        cleaned: List[str] = []
        seen = set()
        for url in image_urls:
            lower = url.lower()
            if not any(ext in lower for ext in (".jpg", ".jpeg", ".png", ".webp", "images", "photo")):
                continue
            if url not in seen:
                seen.add(url)
                cleaned.append(url)
        return cleaned[:10]

    try:
        search_results = safe_search()
        results = search_results.get("results", [])
        source_urls = [r.get("url", "") for r in results if r.get("url")]
        image_urls = _extract_image_urls(results)

        # Fallback: if image fields are missing, provide source pages where images are likely present
        if not image_urls:
            image_urls = source_urls[:5]

        out = PlacePicturesOutput(
            place_name=place_name,
            city=city,
            image_urls=image_urls,
            source_urls=source_urls[:8],
        )
        print(
            f"\033[38;5;208m>>> [TOOL INFO] Resolved {len(image_urls)} image urls for {query_target}\033[0m"
        )
        return out.model_dump_json()
    except Exception as e:
        print(f"\033[38;5;208m>>> [TOOL ERROR] place pictures lookup failed: {e}\033[0m")
        out = PlacePicturesOutput(
            place_name=place_name,
            city=city,
            image_urls=[],
            source_urls=[],
            error=f"Image lookup failed: {str(e)}",
        )
        return out.model_dump_json()
