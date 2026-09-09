from datetime import datetime, timezone

from ai.forecast.confidence import ForecastConfidence
from ai.risk.risk_engine import RiskEngine
from ai.weather.weather_client import WeatherClient


class WeatherAlertEngine:
    """
    Deterministic weather alert engine.

    Alerts are generated from forecast data and the existing
    WeatherGPT Risk Engine.

    The LLM is NOT used to decide whether an alert should
    be raised.
    """

    def __init__(self):
        self.weather_client = WeatherClient()
        self.risk_engine = RiskEngine()
        self.confidence_engine = ForecastConfidence()

    def generate_alerts(
        self,
        location: str,
        days: int = 3,
    ) -> dict:
        """
        Generate weather alerts for a location.

        Checks:
        - overall weather risk
        - extreme/high heat
        - heavy rainfall probability
        - strong winds
        - thunderstorms
        - heavy rain conditions
        """

        if days < 1 or days > 7:
            raise ValueError(
                "Alert forecast days must be between 1 and 7."
            )

        forecast = self.weather_client.get_forecast_data(
            location=location,
            days=days,
            start_day=0,
        )

        if not forecast:
            return {
                "location": location,
                "alerts": [],
                "alert_count": 0,
                "status": "no_alerts",
                "generated_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "source": (
                    "Open-Meteo + WeatherGPT "
                    "deterministic risk engine"
                ),
            }

        alerts = []

        for day_index, day in enumerate(forecast):
            temperature = self._number(
                day.get("temperature_high")
            )

            rain_probability = self._number(
                day.get("rain_probability")
            )

            wind_speed = self._number(
                day.get("wind_speed")
            )

            humidity = self._number(
                day.get("humidity_mean")
            )

            risk = self.risk_engine.assess(
                temperature=temperature,
                precipitation_probability=rain_probability,
                wind_speed=wind_speed,
                humidity=humidity,
            )

            confidence = self.confidence_engine.calculate(
                precipitation_probability=rain_probability,
                forecast_days=max(
                    1,
                    day_index + 1,
                ),
            )

            condition = str(
                day.get("condition") or "Unknown"
            )

            triggers = []

            # ------------------------------------------------------
            # HEAT
            # ------------------------------------------------------

            if (
                temperature is not None
                and temperature >= 40
            ):
                triggers.append("extreme heat")

            elif (
                temperature is not None
                and temperature >= 35
                and risk["overall_risk"]
                in {"high", "extreme"}
            ):
                triggers.append("high heat")

            # ------------------------------------------------------
            # RAIN
            # ------------------------------------------------------

            if (
                rain_probability is not None
                and rain_probability >= 80
            ):
                triggers.append(
                    "heavy rainfall probability"
                )

            # ------------------------------------------------------
            # WIND
            # ------------------------------------------------------

            if (
                wind_speed is not None
                and wind_speed >= 30
            ):
                triggers.append("strong winds")

            # ------------------------------------------------------
            # WEATHER CONDITIONS
            # ------------------------------------------------------

            condition_lower = condition.lower()

            if "thunderstorm" in condition_lower:
                triggers.append("thunderstorm")

            if (
                "heavy rain" in condition_lower
                or "violent rain" in condition_lower
            ):
                triggers.append("heavy rain")

            # ------------------------------------------------------
            # OVERALL RISK
            # ------------------------------------------------------

            if risk["overall_risk"] in {
                "high",
                "extreme",
            }:
                triggers.append(
                    f"{risk['overall_risk']} "
                    "overall weather risk"
                )

            triggers = self._unique(triggers)

            # No significant trigger -> no alert
            if not triggers:
                continue

            severity = self._severity(
                risk["overall_risk"],
                triggers,
            )

            title = self._title(
                risk["overall_risk"],
                triggers,
            )

            message = self._message(
                day=day,
                risk=risk,
                triggers=triggers,
            )

            recommendations = risk.get(
                "recommendations",
                [],
            )

            action = (
                recommendations[0]
                if recommendations
                else self._default_action(severity)
            )

            alerts.append(
                {
                    "date": day.get("date"),
                    "severity": severity,
                    "title": title,
                    "message": message,
                    "action": action,
                    "risk": risk["overall_risk"],
                    "risk_score": risk["score"],
                    "confidence": confidence,
                    "triggers": triggers,
                    "condition": condition,
                }
            )

        return {
            "location": (
                forecast[0].get("location")
                or location
            ),
            "alerts": alerts,
            "alert_count": len(alerts),
            "status": (
                "alerts"
                if alerts
                else "no_alerts"
            ),
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "source": (
                "Open-Meteo + WeatherGPT "
                "deterministic risk engine"
            ),
        }

    # ==================================================================
    # HELPERS
    # ==================================================================

    @staticmethod
    def _number(value):
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        result = []

        for value in values:
            if value not in result:
                result.append(value)

        return result

    @staticmethod
    def _severity(
        overall_risk: str,
        triggers: list[str],
    ) -> str:

        if overall_risk == "extreme":
            return "critical"

        if (
            overall_risk == "high"
            or "thunderstorm" in triggers
            or "heavy rainfall probability" in triggers
            or "strong winds" in triggers
        ):
            return "high"

        return "moderate"

    @staticmethod
    def _title(
        overall_risk: str,
        triggers: list[str],
    ) -> str:

        if "thunderstorm" in triggers:
            return "Thunderstorm Alert"

        if "extreme heat" in triggers:
            return "Extreme Heat Alert"

        if "heavy rainfall probability" in triggers:
            return "Heavy Rain Alert"

        if "strong winds" in triggers:
            return "Strong Wind Alert"

        if "heavy rain" in triggers:
            return "Heavy Rain Alert"

        if overall_risk == "extreme":
            return "Extreme Weather Risk"

        if overall_risk == "high":
            return "High Weather Risk"

        return "Weather Risk Advisory"

    @staticmethod
    def _message(
        day: dict,
        risk: dict,
        triggers: list[str],
    ) -> str:

        date = day.get(
            "date",
            "the forecast period",
        )

        trigger_text = ", ".join(triggers)

        return (
            f"{date}: {trigger_text}. "
            f"WeatherGPT risk level is "
            f"{risk['overall_risk']}."
        )

    @staticmethod
    def _default_action(
        severity: str,
    ) -> str:

        if severity == "critical":
            return (
                "Avoid unnecessary outdoor exposure "
                "and follow local safety guidance."
            )

        if severity == "high":
            return (
                "Use caution and consider postponing "
                "non-essential outdoor activity."
            )

        return (
            "Monitor the weather and keep a backup "
            "plan for outdoor activities."
        )
