from datetime import datetime, timezone
from typing import Any

import httpx

from ai.forecast.confidence import ForecastConfidence
from ai.risk.risk_engine import RiskEngine
from ai.weather.weather_client import WeatherClient


class BestTimeEngine:
    """
    Deterministic activity scheduling engine.

    It evaluates hourly Open-Meteo forecast conditions and selects
    the most suitable time window for an outdoor activity.

    The LLM is not used to calculate the score or choose the time.
    """

    ACTIVITY_LIMITS = {
        "outdoor": {"max_temp": 35, "max_rain": 40, "max_wind": 30},
        "walking": {"max_temp": 35, "max_rain": 40, "max_wind": 30},
        "running": {"max_temp": 32, "max_rain": 30, "max_wind": 25},
        "cycling": {"max_temp": 34, "max_rain": 30, "max_wind": 30},
        "sports": {"max_temp": 32, "max_rain": 30, "max_wind": 25},
        "travel": {"max_temp": 38, "max_rain": 50, "max_wind": 35},
        "outdoor_work": {"max_temp": 35, "max_rain": 40, "max_wind": 30},
        "farming": {"max_temp": 38, "max_rain": 60, "max_wind": 35},
    }

    def __init__(self):
        self.weather_client = WeatherClient()
        self.risk_engine = RiskEngine()
        self.confidence_engine = ForecastConfidence()

    def generate_plan(
        self,
        location: str,
        activity: str = "outdoor",
        days: int = 1,
        start_day: int = 0,
    ) -> dict[str, Any]:
        if days < 1 or days > 7:
            raise ValueError("Best-time forecast days must be between 1 and 7.")

        if start_day < 0 or start_day > 6:
            raise ValueError("Best-time start day must be between 0 and 6.")

        activity_key = activity.strip().lower() or "outdoor"
        if activity_key not in self.ACTIVITY_LIMITS:
            activity_key = "outdoor"

        latitude, longitude, resolved_location = self._coordinates(location)
        hourly = self._hourly_forecast(
            latitude=latitude,
            longitude=longitude,
            days=days,
            start_day=start_day,
        )

        candidates = [
            item for item in hourly
            if item["hour"] >= 5 and item["hour"] <= 20
        ]

        if not candidates:
            return self._empty_result(resolved_location, activity_key)

        scored = [
            self._score_hour(item, activity_key)
            for item in candidates
        ]

        best = max(scored, key=lambda item: item["score"])
        backup = self._select_backup(scored, best)

        confidence = self.confidence_engine.calculate(
            precipitation_probability=best["rain_probability"],
            forecast_days=max(1, start_day + 1),
        )

        risk = self.risk_engine.assess(
            temperature=best["temperature"],
            precipitation_probability=best["rain_probability"],
            wind_speed=best["wind_speed"],
            humidity=best["humidity"],
        )

        return {
            "location": resolved_location,
            "activity": activity_key,
            "date": best["date"],
            "best_time": best["time_range"],
            "best_time_start": best["time_start"],
            "best_time_end": best["time_end"],
            "reason": best["reason"],
            "risk": risk["overall_risk"],
            "risk_score": risk["score"],
            "confidence": confidence,
            "conditions": {
                "temperature": best["temperature"],
                "rain_probability": best["rain_probability"],
                "wind_speed": best["wind_speed"],
                "humidity": best["humidity"],
                "condition": best["condition"],
            },
            "backup_plan": self._backup_text(
                backup=backup,
                activity=activity_key,
            ),
            "backup_time": (
                backup["time_range"] if backup else None
            ),
            "status": (
                "recommended"
                if best["score"] >= 45
                else "caution"
                if best["score"] >= 25
                else "poor_conditions"
            ),
            "source": "Open-Meteo hourly forecast + WeatherGPT deterministic risk engine",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _coordinates(location: str):
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": location,
                    "count": 1,
                    "language": "en",
                    "format": "json",
                },
            )
        response.raise_for_status()
        results = response.json().get("results", [])
        if not results:
            raise ValueError(f"Location '{location}' was not found.")

        result = results[0]
        return (
            float(result["latitude"]),
            float(result["longitude"]),
            result.get("name", location),
        )

    @staticmethod
    def _hourly_forecast(
        latitude: float,
        longitude: float,
        days: int,
        start_day: int,
    ) -> list[dict[str, Any]]:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "hourly": (
                        "temperature_2m,"
                        "relative_humidity_2m,"
                        "precipitation_probability,"
                        "precipitation,"
                        "weather_code,"
                        "wind_speed_10m"
                    ),
                    "forecast_days": min(7, max(1, start_day + days)),
                    "timezone": "auto",
                },
            )
        response.raise_for_status()
        data = response.json()
        hourly = data.get("hourly", {})

        times = hourly.get("time", [])
        temperatures = hourly.get("temperature_2m", [])
        humidity = hourly.get("relative_humidity_2m", [])
        rain_probability = hourly.get("precipitation_probability", [])
        precipitation = hourly.get("precipitation", [])
        weather_codes = hourly.get("weather_code", [])
        wind = hourly.get("wind_speed_10m", [])

        start_index = start_day * 24
        end_index = min(
            len(times),
            start_index + days * 24,
        )

        condition_map = {
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
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }

        result = []

        for index in range(start_index, end_index):
            timestamp = str(times[index])
            date_text = timestamp[:10]
            hour_text = timestamp[11:16]
            hour = int(timestamp[11:13])

            result.append({
                "date": date_text,
                "hour": hour,
                "time_start": hour_text,
                "time_end": f"{(hour + 1) % 24:02d}:00",
                "temperature": float(temperatures[index] or 0),
                "humidity": float(humidity[index] or 0),
                "rain_probability": float(rain_probability[index] or 0),
                "precipitation": float(precipitation[index] or 0),
                "weather_code": int(weather_codes[index] or 0),
                "condition": condition_map.get(
                    int(weather_codes[index] or 0),
                    "Unknown",
                ),
                "wind_speed": float(wind[index] or 0),
            })

        return result

    def _score_hour(
        self,
        item: dict[str, Any],
        activity: str,
    ) -> dict[str, Any]:
        limits = self.ACTIVITY_LIMITS[activity]
        score = 100.0
        reasons = []

        temp = item["temperature"]
        rain = item["rain_probability"]
        wind = item["wind_speed"]
        humidity = item["humidity"]
        code = item["weather_code"]

        if temp > limits["max_temp"]:
            score -= min(35, (temp - limits["max_temp"]) * 4)
            reasons.append("temperature is high")
        elif temp < 15:
            score -= min(20, (15 - temp) * 2)
            reasons.append("temperature is cool")
        else:
            reasons.append("comfortable temperature")

        if rain >= 80:
            score -= 45
            reasons.append("high rain probability")
        elif rain >= limits["max_rain"]:
            score -= 25
            reasons.append("rain is possible")
        else:
            score += 5
            reasons.append("low rain probability")

        if wind >= 50:
            score -= 35
            reasons.append("strong winds")
        elif wind >= limits["max_wind"]:
            score -= 20
            reasons.append("moderate winds")
        else:
            score += 5
            reasons.append("manageable wind")

        if humidity >= 85:
            score -= 15
            reasons.append("high humidity")
        elif humidity <= 75:
            score += 3

        if code in {95, 96, 99}:
            score -= 60
            reasons.append("thunderstorm risk")
        elif code in {65, 82}:
            score -= 35
            reasons.append("heavy rain conditions")

        # Prefer cooler morning/evening periods for outdoor activities.
        if 5 <= item["hour"] <= 8:
            score += 8
        elif 17 <= item["hour"] <= 19:
            score += 6
        elif 11 <= item["hour"] <= 15:
            score -= 5

        item = dict(item)
        item["score"] = round(max(0.0, min(100.0, score)), 1)
        item["time_range"] = (
            f"{item['time_start']}–{item['time_end']}"
        )
        item["reason"] = ", ".join(reasons[:4])
        return item

    @staticmethod
    def _select_backup(
        scored: list[dict[str, Any]],
        best: dict[str, Any],
    ):
        alternatives = [
            item for item in scored
            if (
                item["date"] != best["date"]
                or item["hour"] != best["hour"]
            )
            and abs(item["hour"] - best["hour"]) >= 2
        ]

        if not alternatives:
            alternatives = [
                item for item in scored
                if item["hour"] != best["hour"]
            ]

        if not alternatives:
            return None

        return max(alternatives, key=lambda item: item["score"])

    @staticmethod
    def _backup_text(
        backup: dict[str, Any] | None,
        activity: str,
    ) -> str:
        if not backup:
            return (
                f"No reliable backup period was found for {activity}. "
                "Recheck the forecast before going outdoors."
            )

        return (
            f"If the primary period becomes unsuitable, use "
            f"{backup['date']} {backup['time_range']}. "
            f"Conditions there are expected to be "
            f"{backup['condition'].lower()}, with "
            f"{backup['rain_probability']:.0f}% rain probability "
            f"and wind around {backup['wind_speed']:.0f} km/h."
        )

    @staticmethod
    def _empty_result(location: str, activity: str):
        return {
            "location": location,
            "activity": activity,
            "status": "no_data",
            "best_time": None,
            "backup_plan": (
                "No suitable forecast period was available. "
                "Recheck the forecast before planning the activity."
            ),
            "source": "Open-Meteo hourly forecast",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
