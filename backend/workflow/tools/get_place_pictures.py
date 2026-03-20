from typing import Optional

from langchain.tools import tool


@tool(
    "get_place_pictures",
    description="Retrieve representative pictures/image URLs for a given place or landmark."
)
def get_place_pictures(place_name: str, city: Optional[str] = None) -> str:
    """Return image URLs or metadata that visually represent the specified place."""
    pass
