from datetime import datetime
import os
import logging
from typing import Any, Optional
from .logger import get_logger


def get_current_date_time() -> str:
    return datetime.now().strftime("%A, %B %d, %Y %I:%M %p")


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
    log = logger or get_logger(__name__)

    graphs_dir = os.path.join(os.path.dirname(__file__), "../..", output_dirname)
    os.makedirs(graphs_dir, exist_ok=True)
    output_path = os.path.join(graphs_dir, filename)

    try:
        compiled_graph.get_graph().draw_mermaid_png(output_file_path=output_path)
        log.info("Graph visualization saved to %s", output_path)
        return output_path
    except Exception as exc:
        log.warning("Failed to save graph visualization: %s", exc)
        return None
