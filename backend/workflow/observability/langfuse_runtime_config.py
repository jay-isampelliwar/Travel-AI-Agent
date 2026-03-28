from typing import Any, Dict


def build_agent_runtime_config(
    *,
    thread_id: str,
    user_id: str,
    session_id: str,
) -> Dict[str, Any]:
    """
    Build LangGraph runtime config with request metadata.

    Tracing is done manually in graph nodes (see TravelIntelligenceAgent);
    LangChain CallbackHandler is not used.
    """
    return {
        "configurable": {"thread_id": thread_id},
        "metadata": {
            "session_id": session_id,
            "user_id": user_id,
            "thread_id": thread_id,
        },
    }
