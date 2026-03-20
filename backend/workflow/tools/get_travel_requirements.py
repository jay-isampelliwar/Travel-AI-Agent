from typing import List, Optional

from langchain.tools import tool
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from ..services.tavily import TavilySearchService


class TravelRequirementsInput(BaseModel):
    """Strict input for entry requirement checks."""

    citizenship: str = Field(..., description="Traveler passport country, e.g. 'India'")
    destination_country: str = Field(..., description="Destination country, e.g. 'Japan'")


class TravelRequirementsOutput(BaseModel):
    """Structured travel requirement response."""

    citizenship: str
    destination_country: str
    visa_requirement: str
    passport_validity_rule: str
    vaccination_notes: str
    additional_notes: List[str]
    sources: List[str]
    error: Optional[str] = None


@tool(
    "get_travel_requirements",
    args_schema=TravelRequirementsInput,
    description=(
        "Provide visa, passport validity, vaccination, and entry-regulation guidance for "
        "traveling to a destination country based on citizenship. Returns structured JSON."
    ),
)
def get_travel_requirements(citizenship: str, destination_country: str) -> str:
    """Retrieve high-level travel requirements from web sources."""

    print(
        f"\033[38;5;208m>>> [TOOL START] get_travel_requirements: {citizenship} -> {destination_country}\033[0m"
    )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=3, max=10))
    def safe_search() -> dict:
        tavily = TavilySearchService()
        return tavily.invoke(
            {
                "query": (
                    f"Travel entry requirements for {citizenship} citizens visiting {destination_country}: "
                    "visa rules, passport validity, vaccination requirements, customs and immigration updates, "
                    "official government sources"
                ),
                "max_results": 8,
                "search_depth": "advanced",
            }
        )

    try:
        search_results = safe_search()
        urls = [r.get("url", "") for r in search_results.get("results", []) if r.get("url")]

        result = TravelRequirementsOutput(
            citizenship=citizenship,
            destination_country=destination_country,
            visa_requirement=(
                "Check official embassy/immigration guidance. Visa policy varies by purpose and stay duration."
            ),
            passport_validity_rule=(
                "Many countries require passport validity of 6 months beyond entry/exit dates."
            ),
            vaccination_notes=(
                "Check destination health authority and airline advisories for required/recommended vaccines."
            ),
            additional_notes=[
                "Verify latest immigration forms and e-gate requirements before departure.",
                "Confirm return/onward ticket and proof-of-funds requirements.",
                "Re-check requirements 48 hours before travel due to policy changes.",
            ],
            sources=urls[:5],
        )
        print(
            f"\033[38;5;208m>>> [TOOL INFO] Collected {len(result.sources)} requirement sources\033[0m"
        )
        return result.model_dump_json()
    except Exception as e:
        print(f"\033[38;5;208m>>> [TOOL ERROR] requirements lookup failed: {e}\033[0m")
        result = TravelRequirementsOutput(
            citizenship=citizenship,
            destination_country=destination_country,
            visa_requirement="",
            passport_validity_rule="",
            vaccination_notes="",
            additional_notes=[],
            sources=[],
            error=f"Travel requirements lookup failed: {str(e)}",
        )
        return result.model_dump_json()
