"""Weather Tool — fetches current weather data."""

import time
import logging
import httpx

from langchain.tools import tool

from app.config import settings

logger = logging.getLogger(__name__)


@tool
def weather(location: str) -> str:
    """
    Get current weather for a location. Use this when the user asks about
    weather, temperature, or climate conditions for a specific city or place.

    Args:
        location: City name or location (e.g., "Tokyo", "New York", "London, UK")

    Returns:
        Current weather information including temperature, conditions, humidity.
    """
    start = time.time()
    logger.info(f"[Weather] Fetching weather for: {location}")

    try:
        if settings.weather_api_key:
            return _openweathermap(location)
        else:
            return _wttr_in(location)

    except Exception as e:
        logger.error(f"[Weather] Error: {e}")
        return f"Weather lookup failed for {location}: {str(e)}"
    finally:
        duration = (time.time() - start) * 1000
        logger.info(f"[Weather] Completed in {duration:.1f}ms")


def _wttr_in(location: str) -> str:
    """Free weather API using wttr.in (no key needed)."""
    url = f"https://wttr.in/{location}"
    params = {"format": "j1"}

    with httpx.Client(timeout=10) as client:
        response = client.get(url, params=params)
        data = response.json()

    current = data.get("current_condition", [{}])[0]
    area = data.get("nearest_area", [{}])[0]

    city = area.get("areaName", [{}])[0].get("value", location)
    country = area.get("country", [{}])[0].get("value", "")
    temp_c = current.get("temp_C", "N/A")
    temp_f = current.get("temp_F", "N/A")
    desc = current.get("weatherDesc", [{}])[0].get("value", "N/A")
    humidity = current.get("humidity", "N/A")
    wind_kmph = current.get("windspeedKmph", "N/A")
    feels_like = current.get("FeelsLikeC", "N/A")

    return (
        f"Weather for {city}, {country}:\n"
        f"- Condition: {desc}\n"
        f"- Temperature: {temp_c}°C ({temp_f}°F)\n"
        f"- Feels Like: {feels_like}°C\n"
        f"- Humidity: {humidity}%\n"
        f"- Wind: {wind_kmph} km/h"
    )


def _openweathermap(location: str) -> str:
    """OpenWeatherMap API (requires API key)."""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": settings.weather_api_key,
        "units": "metric",
    }

    with httpx.Client(timeout=10) as client:
        response = client.get(url, params=params)
        data = response.json()

    if data.get("cod") != 200:
        return f"Location not found: {location}"

    main = data.get("main", {})
    weather_info = data.get("weather", [{}])[0]
    wind = data.get("wind", {})

    return (
        f"Weather for {data.get('name', location)}, {data.get('sys', {}).get('country', '')}:\n"
        f"- Condition: {weather_info.get('description', 'N/A')}\n"
        f"- Temperature: {main.get('temp', 'N/A')}°C\n"
        f"- Feels Like: {main.get('feels_like', 'N/A')}°C\n"
        f"- Humidity: {main.get('humidity', 'N/A')}%\n"
        f"- Wind: {wind.get('speed', 'N/A')} m/s"
    )
