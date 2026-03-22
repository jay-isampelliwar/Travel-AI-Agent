from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from langfuse import get_client, propagate_attributes

from api.agent_graph import graph_result_to_agent_response, invoke_agent_graph
from api.deps import get_langfuse, get_travel_agent
from api.schemas.agent import AgentRequest, AgentResponse
from workflow.agent import TravelIntelligenceAgent
from workflow.observability.langfuse_runtime_config import build_agent_runtime_config
from workflow.utils.logger import setup_logging


load_dotenv()
setup_logging()


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.agent = TravelIntelligenceAgent()
        app.state.langfuse = get_client()
        yield
        app.state.langfuse.shutdown()

    app = FastAPI(
        title="Travel Intelligence Agent API",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    @app.post("/agent", response_model=AgentResponse)
    async def run_agent(
        payload: AgentRequest,
        agent: TravelIntelligenceAgent = Depends(get_travel_agent),
        langfuse: Any = Depends(get_langfuse),
    ) -> AgentResponse:
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
                    result = await invoke_agent_graph(
                        agent,
                        user_message=payload.user_message,
                        config=config,
                    )
                except Exception as exc:
                    request_observation.update(
                        level="ERROR",
                        status_message=str(exc),
                    )
                    raise

                response = graph_result_to_agent_response(result)
                request_observation.update(
                    output={"message": response.message},
                )

        langfuse.flush()
        return response

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    # Run the local FastAPI app directly on port 8080 so that
    # ngrok can successfully forward traffic to http://localhost:8080.
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)
