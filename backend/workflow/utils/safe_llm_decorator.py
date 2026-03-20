import functools
from typing import Dict, Callable, Any
from langchain_core.messages import AIMessage
from langchain_core.exceptions import LangChainException
from ..agent_state import AgentState

def safe_llm_call(fallback_msg: str = "Temporary issue, please try again."):
    """Reusable decorator for robust LLM node error handling"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, state: AgentState) -> Dict[str, Any]:
            try:
                return func(self, state)
            except Exception as e:
                thread_id = state.get("configurable", {}).get("thread_id", "unknown")

                # TODO Implement logger here.
                # logger.error(
                #     "LLM node failed",
                #     exc_info=e,
                #     node=func.__name__,
                #     thread_id=thread_id,
                #     msg_count=len(state["messages"])
                # )

                if isinstance(e, LangChainException) and hasattr(e, 'lc_error_code'):
                    lc_code = e.lc_error_code
                    if lc_code in ("MODEL_RATE_LIMIT", "httpx.TimeoutException"):
                        raise  # Re-raise for graph retry_policy
                    elif lc_code == "OUTPUT_PARSING_FAILURE":
                        return {"messages": [AIMessage(content="Parsing issue, rephrasing helps.")]}
                    elif lc_code == "MODEL_AUTHENTICATION":
                        return {"messages": [AIMessage(content="Service down, try later.")]}

                # Generic fallback
                return {"messages": [AIMessage(content=fallback_msg)]}

        return wrapper

    return decorator