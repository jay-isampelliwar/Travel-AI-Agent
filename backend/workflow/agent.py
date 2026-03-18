from typing import Dict, Literal
import logging
from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langfuse.langchain import CallbackHandler
from langfuse import observe
from langgraph.prebuilt import ToolNode, tools_condition
from tenacity import retry_unless_exception_type
from langchain_tavily import TavilySearch
from .constants import (
    PLANNER_NODE,
    SEARCH_NODE,
    CHAT_NODE,
    QUERY_GENERATOR_NODE,
    INIT_NODE,
    INTENT_CLASSIFIER_NODE,
    EMERGENCY_TRAVEL_ASSISTANT_NODE,
    PLAN_TRIP_NODE,
    HOTEL_RESTAURANT_SEARCH_NODE,
    UPDATE_TRIP_NODE,
    TRAVEL_TIME_CALCULATION_NODE,
    HOTEL_BOOKING_NODE,
    SEARCH_ALTERNATIVE_ROUTES_NODE,
    LOCAL_ATTRACTIONS_NODE,
    GET_PLACE_PICTURES_NODE,
    EMERGENCY_TRAVEL_ASSISTANT_INTENT,
    PLAN_TRIP_INTENT,
    HOTEL_RESTAURANT_SEARCH_INTENT,
    UPDATE_TRIP_INTENT,
    TRAVEL_TIME_CALCULATION_INTENT,
    HOTEL_BOOKING_INTENT,
    SEARCH_ALTERNATIVE_ROUTES_INTENT,
    LOCAL_ATTRACTIONS_INTENT,
    GET_PLACE_PICTURES_INTENT,
    CHAT_INTENT,
    INTENT_TYPES,
)
from .agent_state import AgentState
from .prompts import (
    SEARCH_QUERY_GENERATOR_PROMPT,
    SYSTEM_INSTRUCTION,
    TIMING_EXTRACTOR_PROMPTS,
    THINGS_TODO_EXTRACTOR_PROMPTS,
    ROUTE_EXTRACTOR_PROMPTS,
    TRIP_PLANNER_PROMPT,
    INTENT_CLASSIFIER_PROMPTS,

)
from .model import ChatMessage, QueryGeneratorModel, ThingsToDo, TravelRoute, TravelTiming
from .utils import get_current_date_time, format_search_results, has_all_required_trip_fields


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
        self.llm = ChatOpenAI(
            model="gpt-4o-mini"
        )
        self.graph = self._build_graph()
        self.search_service = TavilySearch(max_results=5)
        self.langfuse_handler = CallbackHandler()

    @observe(name=INIT_NODE)
    def _init_node(self, _: AgentState) -> Dict:
        logger.info("%s", INIT_NODE)
        return {
            "current_date_time" : get_current_date_time(),
        }

    @observe(name=INTENT_CLASSIFIER_NODE)
    def _intent_classifier(self, state: AgentState) -> INTENT_TYPES:
        logger.info("%s", INTENT_CLASSIFIER_NODE)

        if not has_all_required_trip_fields(state):
            logger.info("intent=%s", CHAT_INTENT)
            return CHAT_INTENT

        messages = state["messages"]
        messages_for_prompt = messages[-10:] if len(messages) > 10 else messages
        user_context = "\n".join([message.content for message in messages_for_prompt])
        system_prompt = SystemMessage(content=INTENT_CLASSIFIER_PROMPTS.format(context=user_context))
        intent = self.llm.invoke([system_prompt])
        # Normalize intent name to match classifier constants
        intent = intent.content.strip().upper()
        logger.info("intent=%s", intent)

        return intent

    @observe(name=CHAT_NODE)
    def _chat_node(self, state: AgentState) -> Dict:
        logger.info("%s", CHAT_NODE)

        current_date_time = state["current_date_time"]
        source = state.get("source") or ""
        destination = state.get("destination") or ""
        travel_dates = state.get("travel_date") or ""
        duration = str(state.get("travel_duration") or "")
        budget = state.get("budget") or ""

        system_instruction = SystemMessage(
            content=SYSTEM_INSTRUCTION.format(
                current_date_time=current_date_time,
                source=source,
                destination=destination,
                travel_dates=travel_dates,
                duration=duration,
                budget=budget,
            )
        )

        messages = [system_instruction] + state["messages"]
        response: ChatMessage = self.llm.with_structured_output(ChatMessage, strict=True).invoke(messages)

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
        if response.budget:
            result["budget"] = response.budget

        return result

    @observe(name=EMERGENCY_TRAVEL_ASSISTANT_NODE)
    def _emergency_travel_assistant_intent(self, state: AgentState) -> Dict:
        logger.info("%s", EMERGENCY_TRAVEL_ASSISTANT_NODE)
        return {
            **state
        }

    @observe(name=PLAN_TRIP_NODE)
    def _plan_trip_intent(self, state: AgentState) -> Dict:
        logger.info("%s", PLAN_TRIP_NODE)
        return {
            **state
        }

    @observe(name=HOTEL_RESTAURANT_SEARCH_NODE)
    def _hotel_restaurant_search_intent(self, state: AgentState) -> Dict:
        logger.info("%s", HOTEL_RESTAURANT_SEARCH_NODE)
        return {
            **state
        }

    @observe(name=UPDATE_TRIP_NODE)
    def _update_trip_intent(self, state: AgentState) -> Dict:
        logger.info("%s", UPDATE_TRIP_NODE)
        return {
            **state
        }

    @observe(name=TRAVEL_TIME_CALCULATION_NODE)
    def _travel_time_calculation_intent(self, state: AgentState) -> Dict:
        logger.info("%s", TRAVEL_TIME_CALCULATION_NODE)
        return {
            **state
        }

    @observe(name=HOTEL_BOOKING_NODE)
    def _hotel_booking_intent(self, state: AgentState) -> Dict:
        logger.info("%s", HOTEL_BOOKING_NODE)
        return {
            **state
        }

    @observe(name=SEARCH_ALTERNATIVE_ROUTES_NODE)
    def _search_alternative_routes_intent(self, state: AgentState) -> Dict:
        logger.info("%s", SEARCH_ALTERNATIVE_ROUTES_NODE)
        return {
            **state
        }

    @observe(name=LOCAL_ATTRACTIONS_NODE)
    def _local_attractions_intent(self, state: AgentState) -> Dict:
        logger.info("%s", LOCAL_ATTRACTIONS_NODE)
        return {
            **state
        }

    @observe(name=GET_PLACE_PICTURES_NODE)
    def _get_place_pictures_intent(self, state: AgentState) -> Dict:
        logger.info("%s", GET_PLACE_PICTURES_NODE)
        return {
            **state
        }

    @observe(name=QUERY_GENERATOR_NODE)
    def _query_generator(self, state: AgentState) -> Dict:
        logger.info("%s", QUERY_GENERATOR_NODE)

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
        logger.info("%s completed", QUERY_GENERATOR_NODE)

        return {
            "web_search_queries": llm_response.queries,
        }

    @observe(name=SEARCH_NODE)
    def _searcher(self, state: AgentState) -> Dict:
        logger.info("%s", SEARCH_NODE)

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

        logger.info("%s completed", SEARCH_NODE)

        return {
            "travel_timings": travel_timings.to_dict(),
            "transportation": travel_route.to_dict(),
            "things_to_do": things_to_do.to_dict(),
        }

    @observe(name=PLANNER_NODE)
    def _planner(self, state: AgentState) -> Dict:
        logger.info("%s", PLANNER_NODE)

        planner_system_prompt = TRIP_PLANNER_PROMPT.format(
        source         = state["source"],
        destination    = state["destination"],
        travel_date    = state["travel_date"],
        duration_days  = state["travel_duration"],
        travel_timings = state["travel_timings"],
        transportation = state["transportation"],
        things_to_do   = state["things_to_do"],
        )

        llm_response = self.llm.invoke([planner_system_prompt])
        logger.info("%s completed", PLANNER_NODE)

        return {
            "messages": [AIMessage(content=llm_response.content.strip())],
            "full_trip_plan" : llm_response.content.strip(),
        }

    # @observe(name="Router")
    # def _router(self, state: AgentState):

    #     if (
    #             state.get("source")
    #             and state.get("destination")
    #             and state.get("travel_duration")
    #             and state.get("travel_date")
    #     ):
    #         return QUERY_GENERATOR_NODE

    #     return END

    def _build_graph(self) :

        graph_builder = StateGraph(AgentState)


        graph_builder.add_node(INIT_NODE, self._init_node)
        graph_builder.add_node(INTENT_CLASSIFIER_NODE, self._chat_node)
        graph_builder.add_node(CHAT_NODE, self._chat_node)
        graph_builder.add_node(EMERGENCY_TRAVEL_ASSISTANT_NODE, self._emergency_travel_assistant_intent)
        graph_builder.add_node(PLAN_TRIP_NODE, self._plan_trip_intent)
        graph_builder.add_node(HOTEL_RESTAURANT_SEARCH_NODE, self._hotel_restaurant_search_intent)
        graph_builder.add_node(UPDATE_TRIP_NODE, self._update_trip_intent)
        graph_builder.add_node(TRAVEL_TIME_CALCULATION_NODE, self._travel_time_calculation_intent)
        graph_builder.add_node(HOTEL_BOOKING_NODE, self._hotel_booking_intent)
        graph_builder.add_node(SEARCH_ALTERNATIVE_ROUTES_NODE, self._search_alternative_routes_intent)
        graph_builder.add_node(LOCAL_ATTRACTIONS_NODE, self._local_attractions_intent)
        graph_builder.add_node(GET_PLACE_PICTURES_NODE, self._get_place_pictures_intent)


        graph_builder.add_node(QUERY_GENERATOR_NODE, self._query_generator)
        graph_builder.add_node(SEARCH_NODE, self._searcher)
        graph_builder.add_node(PLANNER_NODE, self._planner)


        graph_builder.add_edge(START, INIT_NODE)
        graph_builder.add_edge(INIT_NODE, INTENT_CLASSIFIER_NODE)
        graph_builder.add_conditional_edges(
            INTENT_CLASSIFIER_NODE,
            self._intent_classifier,
            {
                CHAT_INTENT: CHAT_NODE,
                EMERGENCY_TRAVEL_ASSISTANT_INTENT: EMERGENCY_TRAVEL_ASSISTANT_NODE,
                PLAN_TRIP_INTENT: PLAN_TRIP_NODE,
                HOTEL_RESTAURANT_SEARCH_INTENT: HOTEL_RESTAURANT_SEARCH_NODE,
                UPDATE_TRIP_INTENT: UPDATE_TRIP_NODE,
                TRAVEL_TIME_CALCULATION_INTENT: TRAVEL_TIME_CALCULATION_NODE,
                HOTEL_BOOKING_INTENT: HOTEL_BOOKING_NODE,
                SEARCH_ALTERNATIVE_ROUTES_INTENT: SEARCH_ALTERNATIVE_ROUTES_NODE,
                LOCAL_ATTRACTIONS_INTENT: LOCAL_ATTRACTIONS_NODE,
                GET_PLACE_PICTURES_INTENT: GET_PLACE_PICTURES_NODE,
            },
        )

        graph_builder.add_edge(CHAT_NODE, END)
        graph_builder.add_edge(EMERGENCY_TRAVEL_ASSISTANT_NODE, QUERY_GENERATOR_NODE)
        graph_builder.add_edge(PLAN_TRIP_NODE, QUERY_GENERATOR_NODE)
        graph_builder.add_edge(HOTEL_RESTAURANT_SEARCH_NODE, END)
        graph_builder.add_edge(UPDATE_TRIP_NODE, QUERY_GENERATOR_NODE)
        graph_builder.add_edge(TRAVEL_TIME_CALCULATION_NODE, QUERY_GENERATOR_NODE)
        graph_builder.add_edge(HOTEL_BOOKING_NODE, END) # TODO: Implement user details collection for hotel booking
        graph_builder.add_edge(SEARCH_ALTERNATIVE_ROUTES_NODE, SEARCH_NODE)
        graph_builder.add_edge(LOCAL_ATTRACTIONS_NODE, SEARCH_NODE)
        graph_builder.add_edge(GET_PLACE_PICTURES_NODE, SEARCH_NODE)

        graph_builder.add_edge(QUERY_GENERATOR_NODE, SEARCH_NODE)
        graph_builder.add_edge(SEARCH_NODE, PLANNER_NODE)
        graph_builder.add_edge(PLANNER_NODE, END)

        agent_memory = MemorySaver()

        return graph_builder.compile(checkpointer=agent_memory)
