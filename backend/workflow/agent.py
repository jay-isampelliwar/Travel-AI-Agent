from typing import Dict
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.redis import RedisSaver
from langfuse.langchain import CallbackHandler
from langfuse import observe
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.globals import set_llm_cache
from langchain_core.caches import InMemoryCache
from langchain_redis import RedisCache
from .services.caching import get_redis_client

from .constant import (
    CHAT_NODE,
    INIT_NODE,
    TOOLS_NODE,
    INPUT_GUARDRAIL_NODE,
    FOLLOW_UP_QUESTION_NODE,
    OUTPUT_GUARDRAILS_NODE,
    SEARCH_RESULT_MAPPER_NODE,
    MERGER_NODE,
    CHAT_NODE_FALLBACK_MSG,
    INPUT_GUARDRAIL_NODE_FALLBACK_MSG,
    OUTPUT_GUARDRAIL_NODE_FALLBACK_MSG,
    FOLLOW_UP_QUESTION_NODE_FALLBACK_MSG,
)
from .agent_state import AgentState
from .prompts import (
    SYSTEM_INSTRUCTION,
    FOLLOW_UP_SUGGESTIONS_PROMPT,
    INPUT_GUARDRAILS_PROMPT,
    OUTPUT_GUARDRAILS_PROMPT,
)

from .model import FollowUpSuggestions
from workflow.utils.utils import get_current_date_time, bottle_mermaid_png
from .tools import ALL_TOOLS
from .services import LLM, TavilySearchService
from .utils.safe_llm_decorator import safe_llm_call
from .utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def _configure_llm_cache() -> None:
    """Use Redis-backed LLM cache when RedisJSON exists, else fallback."""
    try:
        redis_client = get_redis_client()
        # langchain_redis uses RedisJSON commands (JSON.GET / JSON.SET).
        redis_client.execute_command("JSON.GET", "__cache_healthcheck__", ".")
        set_llm_cache(RedisCache(redis_client=redis_client, ttl=600))
    except Exception as exc:
        logger.warning(
            "Redis LLM cache unavailable (RedisJSON missing or Redis down), using InMemoryCache: %s",
            exc,
        )
        set_llm_cache(InMemoryCache())


_configure_llm_cache()

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
    @safe_llm_call(fallback_msg=INPUT_GUARDRAIL_NODE_FALLBACK_MSG)
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
    @safe_llm_call(fallback_msg=CHAT_NODE_FALLBACK_MSG)
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

        tool_name = ""
        if response.tool_calls:
            tool_call = response.tool_calls[0]
            tool_name = tool_call["name"]

        return {
            "last_tool_call": tool_name,
            "messages": [response]
        }

    @observe(name=OUTPUT_GUARDRAILS_NODE)
    @safe_llm_call(fallback_msg=OUTPUT_GUARDRAIL_NODE_FALLBACK_MSG)
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
    @safe_llm_call(fallback_msg=FOLLOW_UP_QUESTION_NODE_FALLBACK_MSG)
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

    @observe(name=SEARCH_RESULT_MAPPER_NODE)
    @safe_llm_call(fallback_msg="")
    def _search_result_mapper_node(self, state: AgentState) -> Dict:

        # last_message = state["messages"][-1].content
        # current_date_time = state["current_date_time"]
        #
        # system_instruction = FOLLOW_UP_SUGGESTIONS_PROMPT.format(
        #     last_message=last_message,
        #     current_date_time=current_date_time
        # )
        #
        # response = self.llm_with_tools.with_structured_output(FollowUpSuggestions).invoke(
        #     [SystemMessage(content=system_instruction)]
        # )

        return {
            **state
            # "follow_up_questions": response.suggestions
        }

    @observe(name=MERGER_NODE)
    @safe_llm_call(fallback_msg="")
    def _join_node(self, state: AgentState) -> AgentState:
        """
        Combine outputs from both branches.
        Assumes both nodes write to state.
        """

        # # Example: combine outputs safely
        # follow_up = state.get("follow_up_question")
        # mapped_results = state.get("mapped_results")
        #
        # # You can merge into final response
        # final_output = {
        #     "follow_up_question": follow_up,
        #     "mapped_results": mapped_results
        # }
        #
        # state["final_output"] = final_output

        return {
            **state
        }

    def _build_graph(self) :

        graph_builder = StateGraph(AgentState)

        graph_builder.add_node(TOOLS_NODE, ToolNode(ALL_TOOLS))
        graph_builder.add_node(INIT_NODE, self._init_node)
        # graph_builder.add_node(INPUT_GUARDRAIL_NODE, self._input_guardrail_node)
        graph_builder.add_node(CHAT_NODE, self._chat_node)
        graph_builder.add_node(OUTPUT_GUARDRAILS_NODE, self._output_guardrail_node)
        graph_builder.add_node(SEARCH_RESULT_MAPPER_NODE, self._search_result_mapper_node)
        graph_builder.add_node(FOLLOW_UP_QUESTION_NODE, self._follow_up_question_node)
        graph_builder.add_node(MERGER_NODE, self._join_node)


        graph_builder.add_edge(START, INIT_NODE)
        # graph_builder.add_edge(INIT_NODE, INPUT_GUARDRAIL_NODE)
        # graph_builder.add_conditional_edges(
        #     INPUT_GUARDRAIL_NODE,
        #     self._input_guardrail_router,
        #     {
        #         CHAT_NODE: CHAT_NODE,
        #         END: END,
        #     }
        # )

        graph_builder.add_edge(INIT_NODE, CHAT_NODE)
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
        graph_builder.add_edge(OUTPUT_GUARDRAILS_NODE, SEARCH_RESULT_MAPPER_NODE)
        graph_builder.add_edge(FOLLOW_UP_QUESTION_NODE, MERGER_NODE)
        graph_builder.add_edge(SEARCH_RESULT_MAPPER_NODE, MERGER_NODE)
        graph_builder.add_edge(MERGER_NODE, END)

        try:
            redis_client = get_redis_client()
            agent_memory = RedisSaver(redis_client)
        except Exception as exc:
            logger.warning("Redis checkpointer unavailable, falling back to MemorySaver: %s", exc)
            agent_memory = MemorySaver()

        graph = graph_builder.compile(checkpointer=agent_memory)

        bottle_mermaid_png(graph, logger=logger)

        return graph
