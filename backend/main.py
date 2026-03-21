from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict, List
from langchain_core.messages import HumanMessage
from workflow.agent import TravelIntelligenceAgent
from workflow.observability.langfuse_runtime_config import build_agent_runtime_config
from workflow.utils.logger import setup_logging
from dotenv import load_dotenv
from langfuse import get_client, propagate_attributes

load_dotenv()
setup_logging()


class AgentRequest(BaseModel):
    user_message: str
    user_id: str
    thread_id: str
    session_id: str


class AgentResponse(BaseModel):
    message: str
    ui_type: str = "None"
    data: Dict[str, Any]
    follow_up_questions: List[str]


app = FastAPI(title="Travel Intelligence Agent API")

# Create a single agent instance to be reused across requests
agent = TravelIntelligenceAgent()
# Initialize Langfuse client - THIS WAS MISSING
langfuse = get_client()

@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/agent", response_model=AgentResponse)
async def run_agent(payload: AgentRequest) -> AgentResponse:
    config = build_agent_runtime_config(
        thread_id=payload.thread_id,
        user_id=payload.user_id,
        session_id=payload.session_id,
    )
    with langfuse.start_as_current_observation(
        name="agent_request",
        as_type="chain",
        input={"user_message": payload.user_message},
        metadata={"thread_id": payload.thread_id},
    ) as request_observation:
        with propagate_attributes(
            session_id=payload.session_id,
            user_id=payload.user_id,
            metadata={"thread_id": payload.thread_id},
        ):
            try:
                result = await agent.graph.ainvoke(
                    {
                        "messages": [
                            HumanMessage(content=payload.user_message)
                        ],
                    },
                    config=config,
                )
            except Exception as exc:
                request_observation.update(
                    level="ERROR",
                    status_message=str(exc),
                )
                raise
            messages = result.get("messages") or []
            if messages and hasattr(messages[-1], "content"):
                answer = messages[-1].content
            else:
                answer = "I'm sorry, I was unable to generate a proper response. Please try rephrasing your query."

            ui_type = result.get("ui_type", "None")
            data = result.get("hotel_search_results") or {}
            if not isinstance(data, dict):
                data = {}

            follow_up_questions = result.get("follow_up_questions") or []
            if not isinstance(follow_up_questions, list):
                follow_up_questions = []

            request_observation.update(
                output={
                    "message": answer,
                    "ui_type": ui_type,
                    "follow_up_questions_count": len(follow_up_questions),
                }
            )

    # Flush all pending observations before returning
    langfuse.flush()

    return AgentResponse(
        message=answer,
        ui_type=ui_type,
        data=data,
        follow_up_questions=follow_up_questions,
    )


if __name__ == "__main__":
    import uvicorn

    # Run the local FastAPI app directly on port 8080 so that
    # ngrok can successfully forward traffic to http://localhost:8080.
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)