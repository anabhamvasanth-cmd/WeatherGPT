from ai.nlp.query_parser import QueryParser
from ai.llm.response_generator import WeatherResponseGenerator
from ai.weather.weather_client import WeatherClient
from ai.forecast.confidence import ForecastConfidence
from ai.risk.risk_engine import RiskEngine
from ai.risk.what_if import WeatherWhatIf
from ai.decision.decision_engine import DecisionEngine


class ChatService:
    """Coordinate weather queries, forecasting, risk, and decisions."""

    def __init__(self):
        self.query_parser = QueryParser()
        self.weather_client = WeatherClient()
        self.response_generator = WeatherResponseGenerator()
        self.forecast_confidence = ForecastConfidence()
        self.risk_engine = RiskEngine()
        self.what_if_engine = WeatherWhatIf()
        self.decision_engine = DecisionEngine()

    def process(self, user_question: str) -> str:
        """Process a weather question."""

        query = self.query_parser.parse(user_question)

        if not query.location:
            return (
                "Please specify a location so I can retrieve the "
                "weather information."
            )

        if query.intent == "what_if":
            weather_context = self._get_what_if_context(
                location=query.location,
                activity=query.activity,
                temperature=query.hypothetical_temperature,
                rain_probability=query.hypothetical_rain_probability,
                wind_speed=query.hypothetical_wind_speed,
                humidity=query.hypothetical_humidity,
            )

        elif query.intent == "risk":
            weather_context = self._get_risk_context(
                query.location,
                query.forecast_days,
                query.start_day,
                query.activity,
            )

        elif query.intent == "forecast":
            weather_context = self._get_forecast_context(
                query.location,
                query.forecast_days,
                query.start_day,
            )

        else:
            weather_context = self.weather_client.get_current_weather(
                query.location
            )

        enriched_context = f"""
Location: {query.location}
Intent: {query.intent}
Forecast days: {query.forecast_days}
Start day: {query.start_day}
Activity: {query.activity}

{weather_context}
"""

        return self.response_generator.generate_response(
            user_question=user_question,
            weather_context=enriched_context,
        )

    def _get_forecast_context(
        self,
        location: str,
        forecast_days: int,
        start_day: int,
    ) -> str:
        """Retrieve structured forecast information with confidence."""

        forecast_data = self.weather_client.get_forecast_data(
            location=location,
            days=forecast_days,
            start_day=start_day,
        )

        if not forecast_data:
            return "No forecast data available."

        confidence = self.forecast_confidence.calculate(
            forecast_days=forecast_days,
        )

        lines = [
            f"Forecast for {location}:"
        ]

        for day in forecast_data:
            lines.append(
                f"{day['date']}: "
                f"{day['condition']}, "
                f"High {day['temperature_high']} °C, "
                f"Low {day['temperature_low']} °C, "
                f"Rain {day['rain_probability']}%, "
                f"Precipitation {day['precipitation']} mm, "
                f"Max wind {day['wind_speed']} km/h"
            )

        lines.append(
            f"Forecast confidence: {confidence:.2f}"
        )

        return "\n".join(lines)

    def _get_risk_context(
        self,
        location: str,
        forecast_days: int,
        start_day: int,
        activity: str,
    ) -> str:
        """Retrieve forecast, calculate risk, and generate a decision."""

        forecast_data = self.weather_client.get_forecast_data(
            location=location,
            days=forecast_days,
            start_day=start_day,
        )

        if not forecast_data:
            return "No forecast data available."

        confidence = self.forecast_confidence.calculate(
            forecast_days=forecast_days,
        )

        lines = [
            f"Forecast for {location}:"
        ]

        for day in forecast_data:
            lines.append(
                f"{day['date']}: "
                f"{day['condition']}, "
                f"High {day['temperature_high']} °C, "
                f"Low {day['temperature_low']} °C, "
                f"Rain {day['rain_probability']}%, "
                f"Precipitation {day['precipitation']} mm, "
                f"Max wind {day['wind_speed']} km/h"
            )

        day = forecast_data[0]

        risk = self.risk_engine.assess(
            temperature=day["temperature_high"],
            precipitation_probability=day["rain_probability"],
            wind_speed=day["wind_speed"],
        )

        decision = self.decision_engine.evaluate(
            risk_assessment=risk,
            activity=activity,
        )

        lines.append(
            f"Forecast confidence: {confidence:.2f}"
        )

        lines.append("Risk assessment:")

        lines.append(
            f"Overall risk: {risk['overall_risk']}"
        )

        lines.append(
            f"Risk score: {risk['score']}"
        )

        lines.append(
            f"Heat impact: {risk['impacts'].get('heat', 'unknown')}"
        )

        lines.append(
            f"Rain impact: {risk['impacts'].get('rain', 'unknown')}"
        )

        lines.append(
            f"Wind impact: {risk['impacts'].get('wind', 'unknown')}"
        )

        lines.append(
            f"Humidity impact: {risk['impacts'].get('humidity', 'unknown')}"
        )

        lines.append("Decision:")

        lines.append(
            f"Activity: {decision['activity']}"
        )

        lines.append(
            f"Decision: {decision['decision']}"
        )

        lines.append(
            f"Recommendation: {decision['recommendation']}"
        )

        if risk["recommendations"]:
            lines.append("Risk recommendations:")

            for recommendation in risk["recommendations"]:
                lines.append(
                    f"- {recommendation}"
                )

        return "\n".join(lines)

    def _get_what_if_context(
        self,
        location: str,
        activity: str,
        temperature: float | None = None,
        rain_probability: float | None = None,
        wind_speed: float | None = None,
        humidity: float | None = None,
    ) -> str:
        """Calculate risk for a hypothetical weather scenario."""

        supplied_values = [
            temperature,
            rain_probability,
            wind_speed,
            humidity,
        ]

        if all(value is None for value in supplied_values):
            return (
                "No hypothetical weather values were detected. "
                "Please specify a hypothetical temperature, rain "
                "probability, wind speed, or humidity."
            )

        scenario = self.what_if_engine.analyze(
            temperature=temperature,
            precipitation_probability=rain_probability,
            wind_speed=wind_speed,
            humidity=humidity,
        )

        risk = scenario["risk_assessment"]

        decision = self.decision_engine.evaluate(
            risk_assessment=risk,
            activity=activity,
        )

        lines = [
            "Hypothetical weather scenario:",
        ]

        if temperature is not None:
            lines.append(
                f"Hypothetical temperature: {temperature} °C"
            )

        if rain_probability is not None:
            lines.append(
                f"Hypothetical rain probability: "
                f"{rain_probability}%"
            )

        if wind_speed is not None:
            lines.append(
                f"Hypothetical wind speed: {wind_speed} km/h"
            )

        if humidity is not None:
            lines.append(
                f"Hypothetical humidity: {humidity}%"
            )

        lines.append("Risk assessment:")

        lines.append(
            f"Overall risk: {risk['overall_risk']}"
        )

        lines.append(
            f"Risk score: {risk['score']}"
        )

        lines.append(
            f"Heat impact: {risk['impacts'].get('heat', 'unknown')}"
        )

        lines.append(
            f"Rain impact: {risk['impacts'].get('rain', 'unknown')}"
        )

        lines.append(
            f"Wind impact: {risk['impacts'].get('wind', 'unknown')}"
        )

        lines.append(
            f"Humidity impact: "
            f"{risk['impacts'].get('humidity', 'unknown')}"
        )

        lines.append("Decision:")

        lines.append(
            f"Activity: {decision['activity']}"
        )

        lines.append(
            f"Decision: {decision['decision']}"
        )

        lines.append(
            f"Recommendation: {decision['recommendation']}"
        )

        if risk["recommendations"]:
            lines.append("Risk recommendations:")

            for recommendation in risk["recommendations"]:
                lines.append(
                    f"- {recommendation}"
                )

        return "\n".join(lines)
