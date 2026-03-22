from typing import Any

from fastapi import Request

from workflow.agent import TravelIntelligenceAgent


def get_travel_agent(request: Request) -> TravelIntelligenceAgent:
    return request.app.state.agent


def get_langfuse(request: Request) -> Any:
    return request.app.state.langfuse
