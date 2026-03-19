from datetime import datetime
import os
import logging
from typing import Mapping, Any, Optional

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


def bottle_mermaid_png(
    compiled_graph: Any,
    *,
    logger: Optional[logging.Logger] = None,
    filename: str = "travel_agent_graph.png",
    output_dirname: str = "graphs",
) -> Optional[str]:
    """
    Best-effort: render a LangGraph Mermaid diagram to a PNG file.

    Returns the output path on success, otherwise None.
    """
    log = logger or logging.getLogger(__name__)

    graphs_dir = os.path.join(os.path.dirname(__file__), "..", output_dirname)
    os.makedirs(graphs_dir, exist_ok=True)
    output_path = os.path.join(graphs_dir, filename)

    try:
        compiled_graph.get_graph().draw_mermaid_png(output_file_path=output_path)
        log.info("Graph visualization saved to %s", output_path)
        return output_path
    except Exception as exc:
        log.warning("Failed to save graph visualization: %s", exc)
        return None
