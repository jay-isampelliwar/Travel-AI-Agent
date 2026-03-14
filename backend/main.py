from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from workflow.agent import TravelIntelligenceAgent
from dotenv import load_dotenv

load_dotenv()


class AgentRequest(BaseModel):
    user_message: str


app = FastAPI(title="Travel Intelligence Agent API")

# Create a single agent instance to be reused across requests
agent = TravelIntelligenceAgent()
config = {"configurable": {"thread_id": "user_123"}}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/agent", response_model=str)
async def run_agent(payload: AgentRequest) -> str:
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

    return answer


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)

