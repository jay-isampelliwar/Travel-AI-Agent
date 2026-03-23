from typing import Dict
from langchain_core.messages import SystemMessage, AIMessage
from langfuse import get_client
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.redis import RedisSaver
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
from .observability.tracing import (
    DEFAULT_CHAT_MODEL,
    lc_messages_to_trace_input,
    trace_usage_from_message,
)
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
        self.graph = self._build_graph()

    def _init_node(self, state: AgentState) -> Dict:
        logger.info("%s", INIT_NODE)
        logger.info("%s",  (state.get("cycle_count") or 0))
        return {

        }

    @safe_llm_call(fallback_msg=INPUT_GUARDRAIL_NODE_FALLBACK_MSG)
    def _input_guardrail_node(self, state: AgentState) -> Dict:
        lf = get_client()
        user_message = state["messages"][-1].content
        with lf.start_as_current_observation(
            as_type="span",
            name=INPUT_GUARDRAIL_NODE,
            input={"user_message_preview": str(user_message)[:2000]},
        ) as span:
            logger.info("%s", INPUT_GUARDRAIL_NODE)

            prompt = INPUT_GUARDRAILS_PROMPT.format(user_message=user_message)
            with lf.start_as_current_observation(
                as_type="generation",
                name="input_guardrail_llm",
                model=DEFAULT_CHAT_MODEL,
                input=prompt[:16000],
            ) as gen:
                response = self.llm.invoke(prompt)
                gen.update(
                    output=response.content,
                    usage_details=trace_usage_from_message(response),
                )

            classification = response.content.strip().upper()
            ai_message = None
            if classification == "END":
                classification = END
                ai_message = AIMessage(content="I appreciate you reaching out, but I'm not able to continue this conversation. I'm here to help with travel planning in a respectful way. If you have any genuine travel questions, I'd be happy to help with those instead.")
            else:
                classification = CHAT_NODE

            logger.info("Guardrail classification: %s", classification)

            out: Dict = {"input_guardrail_decision": classification}
            if ai_message is not None:
                out["ai_message"] = ai_message
            span.update(
                output={
                    "decision": "END" if classification == END else str(classification),
                    "early_exit": ai_message is not None,
                }
            )
            return out

    def _input_guardrail_router(self, state: AgentState) -> str:
        return state.get("input_guardrail_decision") or CHAT_NODE

    @safe_llm_call(fallback_msg=CHAT_NODE_FALLBACK_MSG)
    def _chat_node(self, state: AgentState) -> Dict:
        lf = get_client()
        with lf.start_as_current_observation(
            as_type="span",
            name=CHAT_NODE,
            input={"message_count": len(state["messages"])},
        ) as span:
            logger.info("%s", CHAT_NODE)

            current_date_time = state["current_date_time"]

            system_instruction = SystemMessage(
                content=SYSTEM_INSTRUCTION.format(
                    current_date_time=current_date_time,
                )
            )

            messages = state["messages"]
            llm_messages = [system_instruction] + messages
            with lf.start_as_current_observation(
                as_type="generation",
                name="chat_llm",
                model=DEFAULT_CHAT_MODEL,
                input=lc_messages_to_trace_input(llm_messages),
            ) as gen:
                response = self.llm_with_tools.invoke(llm_messages)
                gen.update(
                    output={
                        "content": response.content,
                        "tool_calls": response.tool_calls,
                    },
                    usage_details=trace_usage_from_message(response),
                )

            tool_name = ""
            if response.tool_calls:
                tool_call = response.tool_calls[0]
                tool_name = tool_call["name"]

            out = {
                "last_tool_call": tool_name,
                "messages": [response],
            }
            span.update(output={"last_tool_call": tool_name or None})
            return out

    @safe_llm_call(fallback_msg=OUTPUT_GUARDRAIL_NODE_FALLBACK_MSG)
    def _output_guardrail_node(self, state: AgentState) -> Dict:
        lf = get_client()
        with lf.start_as_current_observation(
            as_type="span",
            name=OUTPUT_GUARDRAILS_NODE,
            input={"message_count": len(state["messages"])},
        ) as span:
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
            with lf.start_as_current_observation(
                as_type="generation",
                name="output_guardrail_llm",
                model=DEFAULT_CHAT_MODEL,
                input=prompt[:16000],
            ) as gen:
                response = self.llm.invoke(prompt)
                gen.update(
                    output=response.content,
                    usage_details=trace_usage_from_message(response),
                )

            out = {
                "messages": [response],
                "output_guardrail_applied": True,
            }
            span.update(output={"output_guardrail_applied": True})
            return out

    @safe_llm_call(fallback_msg=FOLLOW_UP_QUESTION_NODE_FALLBACK_MSG)
    def _follow_up_question_node(self, state: AgentState) -> Dict:
        lf = get_client()
        last_message = state["messages"][-1].content
        current_date_time = state["current_date_time"]

        system_instruction = FOLLOW_UP_SUGGESTIONS_PROMPT.format(
            last_message=last_message,
            current_date_time=current_date_time,
        )
        sys_msg = SystemMessage(content=system_instruction)

        with lf.start_as_current_observation(
            as_type="span",
            name=FOLLOW_UP_QUESTION_NODE,
            input={"last_message_preview": str(last_message)[:2000]},
        ) as span:
            with lf.start_as_current_observation(
                as_type="generation",
                name="follow_up_structured_llm",
                model=DEFAULT_CHAT_MODEL,
                input=lc_messages_to_trace_input([sys_msg]),
            ) as gen:
                response = self.llm_with_tools.with_structured_output(
                    FollowUpSuggestions
                ).invoke([sys_msg])
                payload = (
                    response.model_dump()
                    if hasattr(response, "model_dump")
                    else {"suggestions": getattr(response, "suggestions", [])}
                )
                gen.update(output=payload)

            out = {"follow_up_questions": response.suggestions}
            span.update(output={"suggestion_count": len(response.suggestions)})
            return out

    def _tools_node(self, state: AgentState) -> Dict:
        lf = get_client()
        preview = ""
        for message in reversed(state.get("messages") or []):
            if getattr(message, "type", "") == "human":
                preview = str(getattr(message, "content", ""))[:500]
                break
        with lf.start_as_current_observation(
            as_type="span",
            name=TOOLS_NODE,
            input={
                "message_count": len(state.get("messages") or []),
                "last_human_preview": preview,
            },
        ) as obs:
            result = self._tool_node.invoke(state)
            obs.update(output={"result_keys": list(result.keys())})
            return result

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

        try:
            redis_client = get_redis_client()
            agent_memory = RedisSaver(redis_client)
        except Exception as exc:
            logger.warning("Redis checkpointer unavailable, falling back to MemorySaver: %s", exc)
            agent_memory = MemorySaver()

        graph = graph_builder.compile(checkpointer=agent_memory)

        bottle_mermaid_png(graph, logger=logger)

        return graph