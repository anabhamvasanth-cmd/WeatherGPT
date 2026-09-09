from ai.nlp.query_parser import QueryParser
from ai.llm.response_generator import WeatherResponseGenerator
from ai.weather.weather_client import WeatherClient
from ai.forecast.confidence import ForecastConfidence
from ai.risk.risk_engine import RiskEngine
from ai.risk.what_if import WeatherWhatIf
from ai.decision.decision_engine import DecisionEngine
from ai.rag.retriever import WeatherRAG
from ai.language.language_detector import LanguageDetector


class ChatService:
    """
    Main WeatherGPT AI orchestration layer.

    Pipeline:

        User Question
            ↓
        Language Detection
            ↓
        Query Parsing
            ↓
        Weather Retrieval
            ↓
        Risk / Forecast / What-If
            ↓
        Decision Engine
            ↓
        Activity-aware RAG
            ↓
        Gemini explanation
    """

    def __init__(self):
        self.query_parser = QueryParser()

        self.weather_client = WeatherClient()

        self.response_generator = (
            WeatherResponseGenerator()
        )

        self.forecast_confidence = (
            ForecastConfidence()
        )

        self.risk_engine = RiskEngine()

        self.what_if_engine = WeatherWhatIf()

        self.decision_engine = DecisionEngine()

        self.rag = WeatherRAG()

        self.language_detector = (
            LanguageDetector()
        )

    # ==========================================================
    # MAIN PROCESSING
    # ==========================================================

    def process(
        self,
        user_question: str,
    ) -> str:
        """
        Process a complete WeatherGPT question.
        """

        if not user_question or not user_question.strip():
            return (
                "Please enter a weather question."
            )

        # ------------------------------------------------------
        # 1. LANGUAGE DETECTION
        # ------------------------------------------------------

        language = (
            self.language_detector.detect_language(
                user_question
            )
        )

        # ------------------------------------------------------
        # 2. QUERY PARSING
        # ------------------------------------------------------

        query = self.query_parser.parse(
            user_question
        )

        # ------------------------------------------------------
        # 3. LOCATION VALIDATION
        # ------------------------------------------------------

        if not query.location:
            return (
                "Please specify a location so I can "
                "retrieve the weather information."
            )

        # ------------------------------------------------------
        # 4. INTENT PROCESSING
        # ------------------------------------------------------

        if query.intent == "what_if":

            weather_context = (
                self._get_what_if_context(
                    location=query.location,
                    activity=query.activity,
                    temperature=(
                        query.hypothetical_temperature
                    ),
                    rain_probability=(
                        query.hypothetical_rain_probability
                    ),
                    wind_speed=(
                        query.hypothetical_wind_speed
                    ),
                    humidity=(
                        query.hypothetical_humidity
                    ),
                )
            )

        elif query.intent == "risk":

            weather_context = (
                self._get_risk_context(
                    location=query.location,
                    forecast_days=(
                        query.forecast_days
                    ),
                    start_day=query.start_day,
                    activity=query.activity,
                )
            )

        elif query.intent == "forecast":

            weather_context = (
                self._get_forecast_context(
                    location=query.location,
                    forecast_days=(
                        query.forecast_days
                    ),
                    start_day=query.start_day,
                )
            )

        else:

            weather_context = (
                self.weather_client
                .get_current_weather(
                    query.location
                )
            )

        # ------------------------------------------------------
        # 5. RAG
        # ------------------------------------------------------

        rag_context = self._get_rag_context(
            user_question=user_question,
            activity=query.activity,
            intent=query.intent,
        )

        # ------------------------------------------------------
        # 6. BUILD TRUSTED CONTEXT
        # ------------------------------------------------------

        enriched_context = f"""
Location: {query.location}

Intent: {query.intent}

Forecast days: {query.forecast_days}

Start day: {query.start_day}

Activity: {query.activity}

Response language:
{language['name']} ({language['code']})

Verified weather and decision information:
{weather_context}

Retrieved domain knowledge:
{rag_context}
"""

        # ------------------------------------------------------
        # 7. LLM EXPLANATION
        # ------------------------------------------------------

        return (
            self.response_generator.generate_response(
                user_question=user_question,
                weather_context=enriched_context,
            )
        )

    # ==========================================================
    # RAG
    # ==========================================================

    def _get_rag_context(
        self,
        user_question: str,
        activity: str,
        intent: str,
    ) -> str:
        """
        Retrieve supporting domain knowledge.

        RAG receives the user's question together with
        activity and intent.

        It does not receive the calculated weather values
        as part of the retrieval query.
        """

        retrieval_query = (
            f"User weather question: "
            f"{user_question}\n"
            f"Activity: {activity}\n"
            f"Intent: {intent}\n"
            f"Relevant weather risks, impacts, "
            f"recommendations, activity guidance, "
            f"and decision support."
        )

        results = self.rag.search_with_scores(
            query=retrieval_query,
            top_k=3,
        )

        if not results:
            return (
                "No sufficiently relevant domain "
                "knowledge was retrieved."
            )

        lines = []

        for document, score in results:

            lines.append(
                f"[Relevance: {score:.3f}]"
            )

            lines.append(
                document
            )

        return "\n\n".join(lines)

    # ==========================================================
    # FORECAST
    # ==========================================================

    def _get_forecast_context(
        self,
        location: str,
        forecast_days: int,
        start_day: int,
    ) -> str:
        """
        Retrieve forecast information and confidence.
        """

        forecast_data = (
            self.weather_client
            .get_forecast_data(
                location=location,
                days=forecast_days,
                start_day=start_day,
            )
        )

        if not forecast_data:
            return (
                "No forecast data available."
            )

        confidence = (
            self.forecast_confidence.calculate(
                forecast_days=forecast_days,
            )
        )

        lines = [
            f"Forecast for {location}:"
        ]

        for day in forecast_data:

            lines.append(
                f"{day['date']}: "
                f"{day['condition']}, "
                f"High "
                f"{day['temperature_high']} °C, "
                f"Low "
                f"{day['temperature_low']} °C, "
                f"Rain "
                f"{day['rain_probability']}%, "
                f"Precipitation "
                f"{day['precipitation']} mm, "
                f"Max wind "
                f"{day['wind_speed']} km/h, "
                f"Mean humidity "
                f"{day['humidity_mean']}%, "
                f"Max humidity "
                f"{day['humidity_max']}%"
            )

        lines.append(
            f"Forecast confidence: "
            f"{confidence:.2f}"
        )

        return "\n".join(lines)

    # ==========================================================
    # RISK
    # ==========================================================

    def _get_risk_context(
        self,
        location: str,
        forecast_days: int,
        start_day: int,
        activity: str,
    ) -> str:
        """
        Calculate weather risk and activity-specific decision.

        The Risk Engine and Decision Engine are authoritative.
        """

        forecast_data = (
            self.weather_client
            .get_forecast_data(
                location=location,
                days=forecast_days,
                start_day=start_day,
            )
        )

        if not forecast_data:
            return (
                "No forecast data available."
            )

        confidence = (
            self.forecast_confidence.calculate(
                forecast_days=forecast_days,
            )
        )

        lines = [
            f"Forecast for {location}:"
        ]

        # ------------------------------------------------------
        # Forecast information
        # ------------------------------------------------------

        for day in forecast_data:

            lines.append(
                f"{day['date']}: "
                f"{day['condition']}, "
                f"High "
                f"{day['temperature_high']} °C, "
                f"Low "
                f"{day['temperature_low']} °C, "
                f"Rain "
                f"{day['rain_probability']}%, "
                f"Precipitation "
                f"{day['precipitation']} mm, "
                f"Max wind "
                f"{day['wind_speed']} km/h, "
                f"Mean humidity "
                f"{day['humidity_mean']}%, "
                f"Max humidity "
                f"{day['humidity_max']}%"
            )

        # ------------------------------------------------------
        # Select requested forecast day
        # ------------------------------------------------------

        selected_day = forecast_data[0]

        # ------------------------------------------------------
        # Risk calculation
        # ------------------------------------------------------

        risk = self.risk_engine.assess(
            temperature=(
                selected_day[
                    "temperature_high"
                ]
            ),
            precipitation_probability=(
                selected_day[
                    "rain_probability"
                ]
            ),
            wind_speed=(
                selected_day[
                    "wind_speed"
                ]
            ),
            humidity=(
                selected_day[
                    "humidity_mean"
                ]
            ),
        )

        # ------------------------------------------------------
        # Activity decision
        # ------------------------------------------------------

        decision = (
            self.decision_engine.evaluate(
                risk_assessment=risk,
                activity=activity,
            )
        )

        # ------------------------------------------------------
        # Forecast confidence
        # ------------------------------------------------------

        lines.append(
            f"Forecast confidence: "
            f"{confidence:.2f}"
        )

        # ------------------------------------------------------
        # Risk assessment
        # ------------------------------------------------------

        lines.append(
            "Risk assessment:"
        )

        lines.append(
            f"Overall risk: "
            f"{risk['overall_risk']}"
        )

        lines.append(
            f"Risk score: "
            f"{risk['score']}"
        )

        lines.append(
            "Heat impact: "
            f"{risk['impacts'].get(
                'heat',
                'unknown'
            )}"
        )

        lines.append(
            "Rain impact: "
            f"{risk['impacts'].get(
                'rain',
                'unknown'
            )}"
        )

        lines.append(
            "Wind impact: "
            f"{risk['impacts'].get(
                'wind',
                'unknown'
            )}"
        )

        lines.append(
            "Humidity impact: "
            f"{risk['impacts'].get(
                'humidity',
                'unknown'
            )}"
        )

        # ------------------------------------------------------
        # Decision
        # ------------------------------------------------------

        lines.append(
            "Decision:"
        )

        lines.append(
            f"Activity: "
            f"{decision['activity']}"
        )

        lines.append(
            f"Decision: "
            f"{decision['decision']}"
        )

        lines.append(
            f"Recommendation: "
            f"{decision['recommendation']}"
        )

        # ------------------------------------------------------
        # Risk recommendations
        # ------------------------------------------------------

        if risk["recommendations"]:

            lines.append(
                "Risk recommendations:"
            )

            for recommendation in (
                risk["recommendations"]
            ):

                lines.append(
                    f"- {recommendation}"
                )

        return "\n".join(lines)

    # ==========================================================
    # WHAT-IF
    # ==========================================================

    def _get_what_if_context(
        self,
        location: str,
        activity: str,
        temperature: float | None = None,
        rain_probability: float | None = None,
        wind_speed: float | None = None,
        humidity: float | None = None,
    ) -> str:
        """
        Calculate risk for a hypothetical scenario.

        Hypothetical values are explicitly labelled.
        """

        supplied_values = [
            temperature,
            rain_probability,
            wind_speed,
            humidity,
        ]

        if all(
            value is None
            for value in supplied_values
        ):
            return (
                "No hypothetical weather values "
                "were detected. Please specify a "
                "hypothetical temperature, rain "
                "probability, wind speed, or humidity."
            )

        scenario = (
            self.what_if_engine.analyze(
                temperature=temperature,
                precipitation_probability=(
                    rain_probability
                ),
                wind_speed=wind_speed,
                humidity=humidity,
            )
        )

        risk = scenario[
            "risk_assessment"
        ]

        decision = (
            self.decision_engine.evaluate(
                risk_assessment=risk,
                activity=activity,
            )
        )

        lines = [
            "Hypothetical weather scenario:"
        ]

        # ------------------------------------------------------
        # Hypothetical inputs
        # ------------------------------------------------------

        if temperature is not None:

            lines.append(
                "Hypothetical temperature: "
                f"{temperature} °C"
            )

        if rain_probability is not None:

            lines.append(
                "Hypothetical rain probability: "
                f"{rain_probability}%"
            )

        if wind_speed is not None:

            lines.append(
                "Hypothetical wind speed: "
                f"{wind_speed} km/h"
            )

        if humidity is not None:

            lines.append(
                "Hypothetical humidity: "
                f"{humidity}%"
            )

        # ------------------------------------------------------
        # Risk
        # ------------------------------------------------------

        lines.append(
            "Risk assessment:"
        )

        lines.append(
            f"Overall risk: "
            f"{risk['overall_risk']}"
        )

        lines.append(
            f"Risk score: "
            f"{risk['score']}"
        )

        lines.append(
            "Heat impact: "
            f"{risk['impacts'].get(
                'heat',
                'unknown'
            )}"
        )

        lines.append(
            "Rain impact: "
            f"{risk['impacts'].get(
                'rain',
                'unknown'
            )}"
        )

        lines.append(
            "Wind impact: "
            f"{risk['impacts'].get(
                'wind',
                'unknown'
            )}"
        )

        lines.append(
            "Humidity impact: "
            f"{risk['impacts'].get(
                'humidity',
                'unknown'
            )}"
        )

        # ------------------------------------------------------
        # Decision
        # ------------------------------------------------------

        lines.append(
            "Decision:"
        )

        lines.append(
            f"Activity: "
            f"{decision['activity']}"
        )

        lines.append(
            f"Decision: "
            f"{decision['decision']}"
        )

        lines.append(
            f"Recommendation: "
            f"{decision['recommendation']}"
        )

        # ------------------------------------------------------
        # Recommendations
        # ------------------------------------------------------

        if risk["recommendations"]:

            lines.append(
                "Risk recommendations:"
            )

            for recommendation in (
                risk["recommendations"]
            ):

                lines.append(
                    f"- {recommendation}"
                )

        return "\n".join(lines)
