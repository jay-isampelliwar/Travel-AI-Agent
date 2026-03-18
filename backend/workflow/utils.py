from datetime import datetime
from typing import Mapping, Any

from .agent_state import AgentState


def get_current_date_time() -> str:
    return datetime.now().strftime("%A, %B %d, %Y %I:%M %p")


def format_search_results(search_results: list) -> str:
    formatted = []
    for i, result in enumerate(search_results, 1):
        if isinstance(result, dict):
            formatted.append(
                f"[Source {i}]: {result.get('title', 'No Title')}\n"
                f"URL: {result.get('url', '')}\n"
                f"Content: {result.get('content', result.get('snippet', ''))}\n"
            )
        else:
            # result is a plain string
            formatted.append(f"[Source {i}]: {result}\n")
    return "\n---\n".join(formatted)


def has_all_required_trip_fields(state: AgentState | Mapping[str, Any]) -> bool:
    """
    Validate that all required trip fields are present and non-empty.

    Required fields (see AgentState):
    - budget
    - source
    - destination
    - travel_duration
    - travel_date
    """
    # AgentState behaves like a mapping, but we also accept generic mappings for flexibility.
    getter = state.get  # type: ignore[attr-defined]

    required_keys = ["budget", "source", "destination", "travel_duration", "travel_date"]

    for key in required_keys:
        value = getter(key, None)
        if value is None:
            return False
        # For strings and collections, also ensure they are not empty
        if isinstance(value, str) and not value.strip():
            return False

    return True
