from typing import Any, Dict
from langfuse.langchain import CallbackHandler

def build_agent_runtime_config(
    *,
    thread_id: str,
    user_id: str,
    session_id: str,
) -> Dict[str, Any]:
    """
    Build LangGraph runtime config with Langfuse tracing metadata.
    """
    langfuse_handler = CallbackHandler()

    return {
        "configurable": {"thread_id": thread_id},
        "callbacks": [langfuse_handler],
        "metadata": {
            "session_id": session_id,
            # "langfuse_trace_id": session_id,
            "user_id": user_id,
            "thread_id": thread_id,
        },
    }
