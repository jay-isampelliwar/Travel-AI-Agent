from datetime import date as _date_class, datetime
from typing import Any, Dict

import requests
from langchain.tools import tool
from .services import LLM, TavilySearchService


class ToolManager:
    def __init__(self):
        print("Initializing Tool Manager")
        self.tavily_search = TavilySearchService()
        self.llm = LLM()

    def get_tools(self):
        """Public method that returns all available tools."""
        return [
            self._search_flights,
            self._search_hotels,
            self._search_restaurants,
            self._get_weather,

            # self._generate_itinerary,
            # self._estimate_trip_cost,
            # self._get_local_attractions,
            # self._get_travel_requirements,
            # self._packing_suggestions,
            # self._get_place_pictures,
        ]

    @tool()
    def _search_flights(self, source_city: str, destination_city: str, departure_date: str):
        """
        Search for available flights between two cities for a specific departure date.

        This tool should be used when a user wants to find flight options for travel.
        It can return information such as airline name, departure time, arrival time,
        price, duration, and available flight numbers.

        Parameters:
        source_city: The city where the user will start their journey.
        destination_city: The city where the user wants to travel.
        departure_date: The date of travel in YYYY-MM-DD format.
        """
        try:
            parsed_date = datetime.strptime(departure_date, "%Y-%m-%d").date()
        except ValueError:
            return {
                "source_city": source_city,
                "destination_city": destination_city,
                "departure_date": departure_date,
                "error": "Invalid date format. Use YYYY-MM-DD.",
            }

        query = (
            f"Flights {source_city} to {destination_city} on {parsed_date.isoformat()} "
            "- airlines, times, duration, price."
        )

        search_results = self.tavily_search.invoke({"query": query})
        return {
            "source_city": source_city,
            "destination_city": destination_city,
            "departure_date": parsed_date.isoformat(),
            "results": search_results,
        }

    @tool()
    def _search_hotels(self, city: str):
        """
        Find available hotels in a specified city for given check-in and check-out dates.

        This tool should return hotel options including hotel name, price per night,
        ratings, amenities, and distance from key locations or tourist attractions.

        Parameters:
        city: The destination city where the user wants to stay.
        checkin_date: The check-in date in YYYY-MM-DD format.
        checkout_date: The check-out date in YYYY-MM-DD format.
        """
        query = (
            f"Best hotels in {city} - price per night, rating, key amenities, area."
        )

        search_results = self.tavily_search.invoke({"query": query})
        return {
            "city": city,
            "results": search_results,
        }


    @tool()
    def _search_restaurants(self, city: str):
        """
        Find recommended restaurants in a specified city.

        This tool should return restaurant options including name, type of cuisine,
        price range, ratings, and distance from key locations or tourist attractions.

        Parameters:
        city: The destination city where the user is staying.
        """
        query = (
            f"Top restaurants in {city} - cuisine, price range, rating, area."
        )

        search_results = self.tavily_search.invoke({"query": query})
        return {
            "city": city,
            "results": search_results,
        }

    @tool()
    def _get_weather(self, city: str, date: str):
        """
        Retrieve weather information for a given city on a specific date.

        This tool is useful for helping travelers plan activities based on weather
        conditions. It may return temperature, precipitation probability,
        humidity, wind speed, and general weather conditions (sunny, rainy, cloudy).

        Parameters:
        city: The city where weather information is needed.
        date: The date for which the weather forecast is requested, in YYYY-MM-DD format.
        """
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return {
                "city": city,
                "date": date,
                "error": "Invalid date format. Use YYYY-MM-DD.",
            }

        geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
        geocode_params: Dict[str, Any] = {"name": city, "count": 1, "language": "en", "format": "json"}

        try:
            geocode_resp = requests.get(geocode_url, params=geocode_params, timeout=10)
            geocode_resp.raise_for_status()
            geocode_data = geocode_resp.json()
        except Exception as exc:
            return {
                "city": city,
                "date": date,
                "error": f"Failed to geocode city: {exc}",
            }

        results = geocode_data.get("results") or []
        if not results:
            return {
                "city": city,
                "date": date,
                "error": "City not found in geocoding service.",
            }

        location = results[0]
        latitude = location.get("latitude")
        longitude = location.get("longitude")
        resolved_name = location.get("name")
        country = location.get("country")
        timezone = location.get("timezone") or "auto"

        today = _date_class.today()
        if target_date < today:
            base_url = "https://archive-api.open-meteo.com/v1/archive"
        else:
            base_url = "https://api.open-meteo.com/v1/forecast"

        weather_params: Dict[str, Any] = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "start_date": target_date.isoformat(),
            "end_date": target_date.isoformat(),
            "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation_probability", "wind_speed_10m"],
        }

        try:
            weather_resp = requests.get(base_url, params=weather_params, timeout=10)
            weather_resp.raise_for_status()
            weather_data = weather_resp.json()
        except Exception as exc:
            return {
                "city": city,
                "date": date,
                "error": f"Failed to fetch weather data: {exc}",
            }

        hourly = weather_data.get("hourly") or {}
        times = hourly.get("time") or []

        if not times:
            return {
                "city": city,
                "date": date,
                "error": "No weather data available for the requested date.",
            }

        def _avg(values: Any) -> float | None:
            if not isinstance(values, list) or not values:
                return None
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            if not numeric_values:
                return None
            return sum(numeric_values) / len(numeric_values)

        temperature_avg = _avg(hourly.get("temperature_2m"))
        humidity_avg = _avg(hourly.get("relative_humidity_2m"))
        precipitation_prob_avg = _avg(hourly.get("precipitation_probability"))
        wind_speed_avg = _avg(hourly.get("wind_speed_10m"))

        condition: str
        if precipitation_prob_avg is not None and precipitation_prob_avg >= 60:
            condition = "likely rainy"
        elif precipitation_prob_avg is not None and precipitation_prob_avg >= 30:
            condition = "chance of rain"
        elif temperature_avg is not None and temperature_avg >= 25:
            condition = "generally warm or hot"
        elif temperature_avg is not None and temperature_avg <= 5:
            condition = "cold"
        else:
            condition = "mostly clear or cloudy"

        return {
            "summary": condition,
            "temperature_celsius_avg": temperature_avg,
            "humidity_percent_avg": humidity_avg,
        }

    def _generate_itinerary(self, destination: str, days: int, interests: list[str]):
        """
        Generate a day-by-day travel itinerary for a destination.

        This tool creates a structured travel plan including suggested attractions,
        activities, restaurants, and sightseeing spots based on the traveler's
        interests and the length of the trip.

        Parameters:
        destination: The travel destination city or country.
        days: Total number of days for the trip.
        interests: A list of traveler interests such as food, adventure,
        history, nightlife, culture, or shopping.
        """
        pass

    def _get_place_pictures(self, place_name: str, city: str | None = None):
        """
        Retrieve representative pictures for a given place or landmark.

        This tool should return one or more image URLs (or image metadata)
        that visually represent the specified place, suitable for use in a
        travel assistant UI.

        Parameters:
        place_name: Name of the place, landmark, attraction, or neighborhood.
        city: Optional city or region to disambiguate the place if needed.
        """
        pass

    def _estimate_trip_cost(self, destination: str, days: int, budget_level: str):
        """
        Estimate the total cost of a trip to a destination.

        This tool calculates an approximate travel budget including flights,
        accommodation, food, transportation, and activities based on the
        user's budget level.

        Parameters:
        destination: The travel destination.
        days: Number of days for the trip.
        budget_level: Budget category such as 'low', 'medium', or 'luxury'.
        """
        pass

    def _get_local_attractions(self, destination: str):
        """
        Retrieve popular tourist attractions and activities in a destination.

        This tool can return well-known landmarks, cultural spots, museums,
        parks, beaches, markets, and other notable places travelers may want
        to visit while in the destination.

        Parameters:
        destination: The city or region for which attractions are requested.
        """
        pass

    def _get_travel_requirements(self, citizenship: str, destination_country: str):
        """
        Provide travel requirements for entering a specific country.

        This tool helps travelers understand visa requirements, passport rules,
        vaccination requirements, and other travel regulations based on their
        citizenship.

        Parameters:
        citizenship: The traveler's country of citizenship.
        destination_country: The country the traveler wants to visit.
        """
        pass

    def _packing_suggestions(self, destination: str, days: int, weather: str):
        """
        Suggest packing items for a trip based on destination, trip duration,
        and expected weather conditions.

        This tool can recommend clothing, travel accessories, documents,
        electronics, and other essentials needed for the trip.

        Parameters:
        destination: The travel destination.
        days: Number of days for the trip.
        weather: Expected weather conditions such as 'cold', 'rainy', or 'hot'.
        """
        pass