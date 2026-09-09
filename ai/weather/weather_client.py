import httpx


class WeatherClient:
    """Client for retrieving weather information from Open-Meteo."""

    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    def get_coordinates(self, location: str) -> tuple[float, float, str]:
        """Convert a location name into latitude and longitude."""

        response = httpx.get(
            self.GEOCODING_URL,
            params={
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json",
            },
            timeout=10.0,
        )

        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        if not results:
            raise ValueError(f"Location not found: {location}")

        result = results[0]

        return (
            result["latitude"],
            result["longitude"],
            result["name"],
        )

    def get_current_weather(self, location: str) -> str:
        """Retrieve current weather information."""

        latitude, longitude, resolved_location = self.get_coordinates(
            location
        )

        response = httpx.get(
            self.FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "precipitation,"
                    "weather_code,"
                    "wind_speed_10m"
                ),
            },
            timeout=10.0,
        )

        response.raise_for_status()

        data = response.json()
        current = data.get("current", {})

        condition = self._weather_description(
            current.get("weather_code")
        )

        return (
            f"Location: {resolved_location}\n"
            f"Temperature: {current.get('temperature_2m')} °C\n"
            f"Feels like: {current.get('apparent_temperature')} °C\n"
            f"Humidity: {current.get('relative_humidity_2m')}%\n"
            f"Precipitation: {current.get('precipitation')} mm\n"
            f"Condition: {condition}\n"
            f"Wind speed: {current.get('wind_speed_10m')} km/h"
        )

    def get_forecast_data(
        self,
        location: str,
        days: int = 7,
        start_day: int = 0,
    ) -> list[dict]:
        """
        Retrieve structured daily weather forecast data.

        start_day:
            0 = today
            1 = tomorrow
            2 = day after tomorrow
        """

        if days < 1 or days > 7:
            raise ValueError(
                "Forecast days must be between 1 and 7."
            )

        if start_day < 0 or start_day > 7:
            raise ValueError(
                "Start day must be between 0 and 7."
            )

        if start_day + days > 7:
            raise ValueError(
                "The requested forecast period exceeds the "
                "available forecast range."
            )

        latitude, longitude, resolved_location = self.get_coordinates(
            location
        )

        response = httpx.get(
            self.FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "forecast_days": 7,
                "daily": (
                    "weather_code,"
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "precipitation_sum,"
                    "precipitation_probability_max,"
                    "wind_speed_10m_max"
                ),
                "timezone": "auto",
            },
            timeout=10.0,
        )

        response.raise_for_status()

        data = response.json()
        daily = data.get("daily", {})

        dates = daily.get("time", [])
        weather_codes = daily.get("weather_code", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precipitation = daily.get("precipitation_sum", [])
        precipitation_probability = daily.get(
            "precipitation_probability_max",
            [],
        )
        wind = daily.get("wind_speed_10m_max", [])

        end_day = start_day + days

        dates = dates[start_day:end_day]
        weather_codes = weather_codes[start_day:end_day]
        max_temps = max_temps[start_day:end_day]
        min_temps = min_temps[start_day:end_day]
        precipitation = precipitation[start_day:end_day]
        precipitation_probability = precipitation_probability[
            start_day:end_day
        ]
        wind = wind[start_day:end_day]

        forecast_data = []

        for i, date in enumerate(dates):
            forecast_data.append(
                {
                    "location": resolved_location,
                    "date": date,
                    "condition": self._weather_description(
                        weather_codes[i]
                    ),
                    "temperature_high": max_temps[i],
                    "temperature_low": min_temps[i],
                    "rain_probability": precipitation_probability[i],
                    "precipitation": precipitation[i],
                    "wind_speed": wind[i],
                }
            )

        return forecast_data

    def get_forecast(
        self,
        location: str,
        days: int = 7,
        start_day: int = 0,
    ) -> str:
        """Retrieve and format daily weather forecast."""

        forecast_data = self.get_forecast_data(
            location=location,
            days=days,
            start_day=start_day,
        )

        if not forecast_data:
            return "No forecast data available."

        forecast_lines = [
            f"Forecast for {forecast_data[0]['location']}:"
        ]

        for day in forecast_data:
            forecast_lines.append(
                f"{day['date']}: "
                f"{day['condition']}, "
                f"High {day['temperature_high']} °C, "
                f"Low {day['temperature_low']} °C, "
                f"Rain {day['rain_probability']}%, "
                f"Precipitation {day['precipitation']} mm, "
                f"Max wind {day['wind_speed']} km/h"
            )

        return "\n".join(forecast_lines)

    @staticmethod
    def _weather_description(code: int | None) -> str:
        """Convert Open-Meteo weather code to readable text."""

        descriptions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }

        return descriptions.get(
            code,
            "Unknown weather condition",
        )
