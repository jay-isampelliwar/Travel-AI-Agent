from datetime import date as _date_class
from typing import Optional

import requests
from langchain.tools import tool
from pydantic import BaseModel, Field
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


def _average(values: list[float | int | None]) -> Optional[float]:
    """Safe average calculation."""
    numeric = [v for v in values if isinstance(v, (int, float))]
    return sum(numeric) / len(numeric) if numeric else None


class WeatherInput(BaseModel):
    """Strict weather query inputs."""
    city: str = Field(..., description="City name (e.g., 'London', 'New York')")
    date: str = Field(..., description="Date in YYYY-MM-DD format")


class WeatherOutput(BaseModel):
    """Structured weather forecast."""
    resolved_city: str
    resolved_country: Optional[str] = None
    date: str
    summary: str
    temperature_celsius_avg: Optional[float] = None
    feels_like_celsius_avg: Optional[float] = None
    humidity_percent_avg: Optional[float] = None
    precipitation_probability_avg: Optional[float] = None
    wind_speed_kmh_avg: Optional[float] = None
    error: Optional[str] = None


@tool(
    "get_weather",
    args_schema=WeatherInput,
    description="""Get accurate hourly weather forecast for any city/date using Open-Meteo API. 
    Returns avg temperature (°C), precipitation chance (%), humidity, wind (km/h), feels-like, 
    and summary (rainy, sunny, cold, warm). Supports historical (past dates) and forecasts. 
    Use for travel planning, events, outdoor activities.""".strip()
)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.RequestException)
)
def get_weather(city: str, date: str) -> dict:
    """Production weather lookup with retries, structured output, full validation."""

    print(f"\033[38;5;208m>>> [TOOL START] get_weather: {city} on {date}\033[0m")

    try:
        target_date = _date_class.fromisoformat(date)
        if target_date > _date_class.today():
            base_url = "https://api.open-meteo.com/v1/forecast"
        else:
            base_url = "https://archive-api.open-meteo.com/v1/archive"
    except ValueError:
        result = WeatherOutput(
            resolved_city=city, date=date, summary="",
            error="Invalid date format. Use YYYY-MM-DD (e.g., 2024-12-15)."
        )
        return result.model_dump()

    geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
    try:
        resp = requests.get(geocode_url, params={
            "name": city, "count": 1, "language": "en", "format": "json"
        }, timeout=8)
        resp.raise_for_status()
        geocode_data = resp.json()
        results = geocode_data.get("results", [])

        if not results:
            raise ValueError(f"City '{city}' not found")

        location = results[0]
        lat, lon = location["latitude"], location["longitude"]
        resolved_city, country = location.get("name"), location.get("country")
        timezone = location.get("timezone", "auto")

        print(f"\033[38;5;208m>>> [TOOL DEBUG] Geocoded {city} → {resolved_city}, {country} ({lat}, {lon})\033[0m")

    except Exception as e:
        print(f"\033[38;5;208m>>> [TOOL WARN] Geocoding failed for {city}: {e}\033[0m")
        result = WeatherOutput(
            resolved_city=city, date=target_date.isoformat(), summary="",
            error=f"City lookup failed: {str(e)}"
        )
        return result.model_dump()

    weather_params = {
        "latitude": lat, "longitude": lon, "timezone": timezone,
        "start_date": target_date.isoformat(), "end_date": target_date.isoformat(),
        "hourly": [
            "temperature_2m", "apparent_temperature", "relative_humidity_2m",
            "precipitation_probability", "wind_speed_10m"
        ]
    }

    try:
        resp = requests.get(base_url, params=weather_params, timeout=10)
        resp.raise_for_status()
        weather_data = resp.json()
        hourly = weather_data.get("hourly", {})
        times = hourly.get("time", [])

        if not times:
            raise ValueError("No hourly data returned")

        temp_avg = _average(hourly["temperature_2m"])
        feels_avg = _average(hourly["apparent_temperature"])
        humidity_avg = _average(hourly["relative_humidity_2m"])
        precip_avg = _average(hourly["precipitation_probability"])
        wind_avg = _average(hourly["wind_speed_10m"])

        if precip_avg and precip_avg >= 60:
            summary = "likely rainy/heavy showers"
        elif precip_avg and precip_avg >= 30:
            summary = "showers possible"
        elif temp_avg and temp_avg >= 25:
            summary = "warm/hot and sunny"
        elif temp_avg and temp_avg <= 5:
            summary = "cold"
        else:
            summary = "mild/cool, partly cloudy"

        result = WeatherOutput(
            resolved_city=resolved_city,
            resolved_country=country,
            date=target_date.isoformat(),
            summary=summary,
            temperature_celsius_avg=temp_avg,
            feels_like_celsius_avg=feels_avg,
            humidity_percent_avg=humidity_avg,
            precipitation_probability_avg=precip_avg,
            wind_speed_kmh_avg=wind_avg
        )

        print(f"\033[38;5;208m>>> [TOOL INFO] Weather {resolved_city}: {summary}, {temp_avg:.1f}°C\033[0m")
        return result.model_dump()

    except Exception as e:
        print(f"\033[38;5;208m>>> [TOOL ERROR] Weather fetch failed: {str(e)}\033[0m")
        result = WeatherOutput(
            resolved_city=resolved_city or city,
            date=target_date.isoformat(),
            summary="", error=f"Weather data unavailable: {str(e)}"
        )
        return result.model_dump()
