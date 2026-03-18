
from typing import Literal

INIT_NODE = "init"
INTENT_CLASSIFIER_NODE = "intent_classifier"
QUERY_GENERATOR_NODE = "query_generator"
PLANNER_NODE = "planner"
SEARCH_NODE = "search"

# Intent-specific node names
CHAT_NODE = "chat"
EMERGENCY_TRAVEL_ASSISTANT_NODE = "emergency_travel_assistant"
PLAN_TRIP_NODE = "plan_trip"
HOTEL_RESTAURANT_SEARCH_NODE = "hotel_restaurant_search"
UPDATE_TRIP_NODE = "update_trip"
TRAVEL_TIME_CALCULATION_NODE = "travel_time_calculation"
HOTEL_BOOKING_NODE = "hotel_booking"
SEARCH_ALTERNATIVE_ROUTES_NODE = "search_alternative_routes"
LOCAL_ATTRACTIONS_NODE = "local_attractions"
GET_PLACE_PICTURES_NODE = "get_place_pictures"

# Union type of all supported intent node names
INTENT_TYPES = Literal[
    "chat",
    "emergency_travel_assistant",
    "plan_trip",
    "hotel_restaurant_search",
    "update_trip",
    "travel_time_calculation",
    "hotel_booking",
    "search_alternative_routes",
    "local_attractions",
    "get_place_pictures",
]