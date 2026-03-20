from typing import Dict
import logging
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langfuse.langchain import CallbackHandler
from langfuse import observe
from langgraph.prebuilt import ToolNode, tools_condition
from .constants import (
    CHAT_NODE,
    INIT_NODE,
    TOOLS_NODE,
    INPUT_GUARDRAIL_NODE,
    FOLLOW_UP_QUESTION_NODE,
    OUTPUT_GUARDRAILS_NODE,
)
from .agent_state import AgentState
from .prompts import (
    SYSTEM_INSTRUCTION,
    FOLLOW_UP_SUGGESTIONS_PROMPT,
    INPUT_GUARDRAILS_PROMPT,
    OUTPUT_GUARDRAILS_PROMPT,
)

from .model import FollowUpSuggestions
from .utils import get_current_date_time, bottle_mermaid_png
from .tools import ALL_TOOLS
from .services import LLM, TavilySearchService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)


class TravelIntelligenceAgent:

    def __init__(self):
        self.llm = LLM()
        self.llm_with_tools = self.llm.bind_tools(ALL_TOOLS)
        self.search_service = TavilySearchService()
        self.langfuse_handler = CallbackHandler()
        self.graph = self._build_graph()

    @observe(name=INIT_NODE)
    def _init_node(self, state: AgentState) -> Dict:
        logger.info("%s", INIT_NODE)
        logger.info("%s",  (state.get("cycle_count") or 0))
        return {
            "current_date_time" : get_current_date_time(),
            "cycle_count": (state.get("cycle_count") or 0) + 1
        }

    @observe(name=INPUT_GUARDRAIL_NODE)
    def _input_guardrail_node(self, state: AgentState) -> Dict:
        logger.info("%s", INPUT_GUARDRAIL_NODE)

        user_message = state["messages"][-1].content
        prompt = INPUT_GUARDRAILS_PROMPT.format(user_message=user_message)
        response = self.llm.invoke(prompt)

        classification = response.content.strip().upper()
        if classification == "END":
            classification = END
        else:
            classification = CHAT_NODE

        logger.info("Guardrail classification: %s", classification)

        return {"input_guardrail_decision": classification}

    @observe(name="input_guardrail_router")
    def _input_guardrail_router(self, state: AgentState) -> str:
        return state.get("input_guardrail_decision") or CHAT_NODE

    @observe(name=CHAT_NODE)
    def _chat_node(self, state: AgentState) -> Dict:
        logger.info("%s", CHAT_NODE)

        current_date_time = state["current_date_time"]

        system_instruction = SystemMessage(
            content=SYSTEM_INSTRUCTION.format(
                current_date_time=current_date_time,
            )
        )

        messages = state["messages"]
        response = self.llm_with_tools.invoke([system_instruction] + messages)

        return {
            "messages": [response]
        }

    @observe(name=OUTPUT_GUARDRAILS_NODE)
    def _output_guardrail_node(self, state: AgentState) -> Dict:
        logger.info("%s", OUTPUT_GUARDRAILS_NODE)

        user_message = ""
        for message in reversed(state["messages"]):
            if getattr(message, "type", "") == "human":
                user_message = message.content
                break

        assistant_draft = state["messages"][-1].content
        prompt = OUTPUT_GUARDRAILS_PROMPT.format(
            user_message=user_message,
            assistant_draft=assistant_draft,
        )
        response = self.llm.invoke(prompt)

        return {
            "messages": [response],
            "output_guardrail_applied": True,
        }

    @observe(name=FOLLOW_UP_QUESTION_NODE)
    def _follow_up_question_node(self, state: AgentState) -> Dict:
        
        last_message = state["messages"][-1].content
        current_date_time = state["current_date_time"]

        system_instruction = FOLLOW_UP_SUGGESTIONS_PROMPT.format(
            last_message=last_message,
            current_date_time=current_date_time
            )
            
        response = self.llm_with_tools.with_structured_output(FollowUpSuggestions).invoke(
            [SystemMessage(content=system_instruction)]
            )

        return {
            "follow_up_questions": response.suggestions
        }


    def _build_graph(self) :

        graph_builder = StateGraph(AgentState)

        graph_builder.add_node(TOOLS_NODE, ToolNode(ALL_TOOLS))
        graph_builder.add_node(INIT_NODE, self._init_node)
        graph_builder.add_node(INPUT_GUARDRAIL_NODE, self._input_guardrail_node)
        graph_builder.add_node(CHAT_NODE, self._chat_node)
        graph_builder.add_node(OUTPUT_GUARDRAILS_NODE, self._output_guardrail_node)
        graph_builder.add_node(FOLLOW_UP_QUESTION_NODE, self._follow_up_question_node)


        graph_builder.add_edge(START, INIT_NODE)
        graph_builder.add_edge(INIT_NODE, INPUT_GUARDRAIL_NODE)
        graph_builder.add_conditional_edges(
            INPUT_GUARDRAIL_NODE,
            self._input_guardrail_router,
            {
                CHAT_NODE: CHAT_NODE,
                END: END,
            }
        )

        graph_builder.add_conditional_edges(
            CHAT_NODE,
            tools_condition,
            {
                TOOLS_NODE: TOOLS_NODE,
                END: OUTPUT_GUARDRAILS_NODE
            }
        )

        graph_builder.add_edge(TOOLS_NODE, CHAT_NODE)
        graph_builder.add_edge(OUTPUT_GUARDRAILS_NODE, FOLLOW_UP_QUESTION_NODE)
        graph_builder.add_edge(FOLLOW_UP_QUESTION_NODE, END)

        agent_memory = MemorySaver()

        graph = graph_builder.compile(checkpointer=agent_memory)

        bottle_mermaid_png(graph, logger=logger)

        return graph
