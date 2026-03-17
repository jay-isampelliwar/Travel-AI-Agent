from datetime import datetime
from typing import Dict, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langfuse.langchain import CallbackHandler
from langfuse import observe
from langgraph.prebuilt import ToolNode, tools_condition
from tenacity import retry_unless_exception_type
from langchain_tavily import TavilySearch
from .constants import PLANNER_NODE, SEARCH_NODE, CHAT_NODE, QUERY_GENERATOR_NODE, INIT_NODE
from .agent_state import AgentState
from .prompts import (
    SEARCH_QUERY_GENERATOR_PROMPT,
    SYSTEM_INSTRUCTION,
    TIMING_EXTRACTOR_PROMPTS,
    THINGS_TODO_EXTRACTOR_PROMPTS,
    ROUTE_EXTRACTOR_PROMPTS,
    TIPS_EXTRACTOR_PROMPT,
    TRIP_PLANNER_PROMPT,

)
from .model import ChatMessage, TravelTiming, TravelRoute, ThingsToDo, QueryGeneratorModel
from .utils import get_current_date_time, format_search_results


class TravelIntelligenceAgent:

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini"
            # model="gpt-4o",
            # api_key="",
            # base_url="http://127.0.0.1:1234/v1",
        )
        self.graph = self._build_graph()
        self.search_service = TavilySearch(max_results=5)
        self.langfuse_handler = CallbackHandler()

    @observe(name=INIT_NODE)
    def _init_node(self, _: AgentState) -> Dict:
        return {
            "current_date_time" : get_current_date_time(),
        }

    @observe(name=CHAT_NODE)
    def _chat_node(self, state: AgentState) -> Dict:

        current_date_time = state["current_date_time"]
        system_instruction = SystemMessage(content=SYSTEM_INSTRUCTION.format(current_date_time=current_date_time))

        messages = [system_instruction] + state["messages"]
        response = self.llm.with_structured_output(ChatMessage, strict=True).invoke(messages)

        result = {
            "messages": [AIMessage(content=response.ai_message)]
        }

        if response.source:
            result["source"] = response.source
        if response.destination:
            result["destination"] = response.destination
        if response.travel_duration:
            result["travel_duration"] = response.travel_duration
        if response.travel_date:
            result["travel_date"] = response.travel_date

        return result

    @observe(name=QUERY_GENERATOR_NODE)
    def _query_generator(self, state: AgentState) -> Dict:

        print(f"NODE => {QUERY_GENERATOR_NODE}")

        user_query = state["messages"][-1].content
        source = state["source"]
        destination = state["destination"]
        travel_duration = state["travel_duration"]
        travel_date = state["travel_date"]

        system_prompt = SystemMessage(
            content=SEARCH_QUERY_GENERATOR_PROMPT.format(
                source=source,
                destination=destination,
                duration_days=travel_duration,
                travel_date=travel_date,
            )
        )

        llm_response : QueryGeneratorModel = self.llm.with_structured_output(QueryGeneratorModel, strict=True).invoke([system_prompt] + [user_query])

        print("Query node completed execution")
        print(llm_response.to_dict())

        return {
            "web_search_queries": llm_response.queries,
        }

    @observe(name=SEARCH_NODE)
    def _searcher(self, state: AgentState) -> Dict:

        web_search_queries = state["web_search_queries"]

        # Loop through each query and accumulate results
        all_search_results = []
        for query in web_search_queries:
            search_results = self.search_service.invoke({"query": query})
            all_search_results.extend(search_results)

        formatted_context = format_search_results(all_search_results)

        travel_timings = self.llm.with_structured_output(TravelTiming, strict=True).invoke(
            TIMING_EXTRACTOR_PROMPTS.format(
                context=formatted_context,
                travel_date=state["travel_date"],
                destination=state["destination"],
                duration_days=state["travel_duration"],
            )
        )

        travel_route = self.llm.with_structured_output(TravelRoute, strict=True).invoke(
            ROUTE_EXTRACTOR_PROMPTS.format(
                context=formatted_context,
                source=state["source"],
                destination=state["destination"],
                travel_date=state["travel_date"],
            )
        )

        things_to_do = self.llm.with_structured_output(ThingsToDo, strict=True).invoke(
            THINGS_TODO_EXTRACTOR_PROMPTS.format(
                context=formatted_context,
                destination=state["destination"],
                travel_date=state["travel_date"],
                duration_days=state["travel_duration"],
            )
        )


        print("Search node completed execution")

        return {
            "travel_timings": travel_timings.to_dict(),
            "transportation": travel_route.to_dict(),
            "things_to_do": things_to_do.to_dict(),
        }

    @observe(name=PLANNER_NODE)
    def _planner(self, state: AgentState) -> Dict:

        planner_system_prompt = TRIP_PLANNER_PROMPT.format(
        source         = state["source"],
        destination    = state["destination"],
        travel_date    = state["travel_date"],
        duration_days  = state["travel_duration"],
        travel_timings = state["travel_timings"],
        transportation = state["transportation"],
        things_to_do   = state["things_to_do"],
        travel_tips    = state["travel_tips"],
        )

        llm_response = self.llm.invoke([planner_system_prompt])

        print("Planner node completed execution")

        return {
            "messages": [AIMessage(content=llm_response.content.strip())],
            "full_trip_plan" : llm_response.content.strip(),
        }

    @observe(name="Router")
    def _router(self, state: AgentState):

        if (
                state.get("source")
                and state.get("destination")
                and state.get("travel_duration")
                and state.get("travel_date")
        ):
            return QUERY_GENERATOR_NODE

        return END

    def _build_graph(self) :

        graph_builder = StateGraph(AgentState)


        graph_builder.add_node(INIT_NODE, self._init_node)
        graph_builder.add_node(CHAT_NODE, self._chat_node)
        graph_builder.add_node(QUERY_GENERATOR_NODE, self._query_generator)
        graph_builder.add_node(SEARCH_NODE, self._searcher)
        graph_builder.add_node(PLANNER_NODE, self._planner)

        graph_builder.add_edge(START, INIT_NODE),
        graph_builder.add_edge(INIT_NODE, CHAT_NODE),
        graph_builder.add_conditional_edges(CHAT_NODE, self._router, {
            QUERY_GENERATOR_NODE: QUERY_GENERATOR_NODE,
            END: END
        })
        graph_builder.add_edge(QUERY_GENERATOR_NODE, SEARCH_NODE),
        graph_builder.add_edge(SEARCH_NODE, PLANNER_NODE),
        graph_builder.add_edge(PLANNER_NODE, END),

        agent_memory = MemorySaver()

        return graph_builder.compile(checkpointer=agent_memory)
