from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from workflow.agent import TravelIntelligenceAgent


class AgentRequest(BaseModel):
    user_message: str


app = FastAPI(title="Travel Intelligence Agent API")

# Create a single agent instance to be reused across requests
agent = TravelIntelligenceAgent()
config = {"configurable": {"thread_id": "user_123"}}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/agent")
async def run_agent(payload: AgentRequest):
    async def event_stream():
        async for event in agent.graph.astream(
            {
                "messages": [
                    HumanMessage(
                        content=payload.user_message,
                    )
                ],
            },
            config=config,
            stream_mode="messages",
        ):
            for node_state in event.values():
                messages = node_state.get("messages", [])
                for message in messages:
                    if isinstance(message, AIMessage):
                        yield message.content

    return StreamingResponse(event_stream(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)

