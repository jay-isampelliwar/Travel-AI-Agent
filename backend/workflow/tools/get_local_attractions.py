from langchain.tools import tool


@tool(
    "get_local_attractions",
    description="Retrieve popular tourist attractions and activities in a destination including landmarks, museums, parks, and markets."
)
def get_local_attractions(destination: str) -> str:
    """Retrieve well-known landmarks, cultural spots, museums, parks, beaches, markets, and notable places."""
    pass
