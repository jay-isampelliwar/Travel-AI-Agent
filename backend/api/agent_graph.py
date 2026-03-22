from typing import Any, Dict, List

from langchain_core.messages import HumanMessage

from workflow.agent import TravelIntelligenceAgent

from .schemas.agent import AgentResponse


def _message_from_graph_result(result: Dict[str, Any]) -> str:
    messages = result.get("messages") or []
    if messages and hasattr(messages[-1], "content"):
        return messages[-1].content
    return (
        "I'm sorry, I was unable to generate a proper response. "
        "Please try rephrasing your query."
    )


def _coerce_hotel_data(result: Dict[str, Any]) -> Dict[str, Any]:
    data = result.get("hotel_search_results") or {}
    return data if isinstance(data, dict) else {}


def _coerce_follow_up_questions(result: Dict[str, Any]) -> List[str]:
    items = result.get("follow_up_questions") or []
    return items if isinstance(items, list) else []


def graph_result_to_agent_response(result: Dict[str, Any]) -> AgentResponse:
    return AgentResponse(
        message=_message_from_graph_result(result),
        ui_type=result.get("ui_type", "None"),
        data=_coerce_hotel_data(result),
        follow_up_questions=_coerce_follow_up_questions(result),
    )


async def invoke_agent_graph(
    agent: TravelIntelligenceAgent,
    *,
    user_message: str,
    config: Any,
) -> Dict[str, Any]:
    return await agent.graph.ainvoke(
        {"messages": [HumanMessage(content=user_message)]},
        config=config,
    )
