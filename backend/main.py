from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict, List
from langchain_core.messages import HumanMessage
from workflow.agent import TravelIntelligenceAgent
from dotenv import load_dotenv

load_dotenv()


class AgentRequest(BaseModel):
    user_message: str


class AgentResponse(BaseModel):
    message: str
    ui_type: str = "None"
    data: Dict[str, Any]
    follow_up_questions: List[str]

app = FastAPI(title="Travel Intelligence Agent API")

# Create a single agent instance to be reused across requests
agent = TravelIntelligenceAgent()
config = {"configurable": {"thread_id": "user_123"}}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/agent", response_model=AgentResponse)
async def run_agent(payload: AgentRequest) -> AgentResponse:
    result = agent.graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=payload.user_message,
                )
            ],
        },
        config=config,
    )

    answer = result["messages"][-1].content

    # For now, return the original message with dummy values
    # for ui_type, data, and follow_up_questions.
    return AgentResponse(
        message=answer,
        ui_type="None",
        data={},
        follow_up_questions=["", ""],
    )


if __name__ == "__main__":
    import uvicorn

    # Run the local FastAPI app directly on port 8080 so that
    # ngrok can successfully forward traffic to http://localhost:8080.
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)

