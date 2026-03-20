from langchain.tools import tool


@tool(
    "get_travel_requirements",
    description="Provide visa, passport, vaccination, and travel regulation requirements for entering a country based on citizenship."
)
def get_travel_requirements(citizenship: str, destination_country: str) -> str:
    """Provide travel entry requirements including visa rules, passport rules, and vaccination requirements."""
    pass
