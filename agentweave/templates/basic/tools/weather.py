"""
Weather tool for getting current weather information.
"""

import logging
import os

import httpx
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from .registry import register_tool

logger = logging.getLogger(__name__)


class WeatherInput(BaseModel):
    """Input schema for the weather tool."""

    location: str = Field(
        description="The city name or location to get weather information for.",
    )


@register_tool
class WeatherTool(BaseTool):
    """Tool for getting current weather information."""

    name: str = "weather"
    description: str = "A tool to get current weather information for a specified location. Input should be a city name or location."
    args_schema: type[BaseModel] = WeatherInput
    api_key: str | None = None

    def __init__(self, api_key: str | None = None):
        """Initialize the weather tool."""
        super().__init__()
        # Try to get API key from parameter or environment
        self.api_key = api_key or os.environ.get("OPENWEATHER_API_KEY")

        # Check if the API key is valid (not None or the placeholder)
        if not self.api_key:
            logger.warning("No OpenWeather API key provided. Weather tool will return mock data.")
            self.api_key = None  # Explicitly set to None if invalid
        elif self.api_key == "your_openweather_api_key_here":
            logger.warning(
                "Using placeholder OpenWeather API key. Weather tool will return mock data."
            )
            self.api_key = None  # Treat placeholder as invalid
        else:
            logger.info(f"Weather tool initialized with API key: {self.api_key[:4]}...")

    def _run(self, location: str) -> str:
        """Get weather information for a location."""
        try:
            # Handle the case where location might be passed as a dictionary
            if isinstance(location, dict):
                # Try to extract location from various possible fields
                loc = location.get("location") or location.get("query") or location.get("input")
                if not loc:
                    # If no recognized field, try to use the first value
                    values = list(location.values())
                    loc = values[0] if values else None

                if not loc:
                    return "Error: No location provided. Please specify a city or location."

                # Use the extracted location
                location = loc

            logger.info(f"Weather request for location: {location}")

            # If the API key is None or empty, use mock data
            if not self.api_key:
                logger.info(f"Using mock weather data for {location}")
                return self._mock_weather(location)

            # Make API request to OpenWeatherMap
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric",  # Use metric units (Celsius)
            }

            logger.info(f"Requesting weather data for {location}")
            response = httpx.get(url, params=params, timeout=10.0)

            if response.status_code != 200:
                logger.error(f"OpenWeatherMap API error: {response.status_code} - {response.text}")
                return f"Error getting weather: {response.status_code} - {response.text}"

            data = response.json()

            # Format the weather information
            weather_description = data["weather"][0]["description"]
            temperature = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]

            return (
                f"Weather in {location}: {weather_description}\n"
                f"Temperature: {temperature}°C (feels like {feels_like}°C)\n"
                f"Humidity: {humidity}%\n"
                f"Wind Speed: {wind_speed} m/s"
            )

        except Exception as e:
            logger.error(f"Error getting weather for '{location}': {str(e)}")
            return f"Error getting weather for {location}: {str(e)}"

    def _mock_weather(self, location: str) -> str:
        """Return mock weather data for testing purposes."""
        return (
            f"Weather in {location}: Partly cloudy\n"
            f"Temperature: 22°C (feels like 24°C)\n"
            f"Humidity: 65%\n"
            f"Wind Speed: 3.5 m/s\n"
            f"Note: This is mock data as no API key was provided."
        )

    async def _arun(self, location: str) -> str:
        """Get weather information asynchronously."""
        return self._run(location)


# Example of using the tool
if __name__ == "__main__":
    weather_tool = WeatherTool()
    result = weather_tool.invoke({"location": "London"})
    print(result)
