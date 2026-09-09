import re
from typing import Optional


class WeatherQuery:
    """Structured representation of a weather-related user query."""

    def __init__(
        self,
        location: Optional[str] = None,
        intent: str = "general",
        forecast_days: int = 1,
        start_day: int = 0,
        activity: str = "outdoor",
        hypothetical_temperature: Optional[float] = None,
        hypothetical_rain_probability: Optional[float] = None,
        hypothetical_wind_speed: Optional[float] = None,
        hypothetical_humidity: Optional[float] = None,
    ):
        self.location = location
        self.intent = intent
        self.forecast_days = forecast_days
        self.start_day = start_day
        self.activity = activity
        self.hypothetical_temperature = (
            hypothetical_temperature
        )
        self.hypothetical_rain_probability = (
            hypothetical_rain_probability
        )
        self.hypothetical_wind_speed = (
            hypothetical_wind_speed
        )
        self.hypothetical_humidity = (
            hypothetical_humidity
        )

    def __repr__(self) -> str:
        return (
            f"WeatherQuery(location={self.location!r}, "
            f"intent={self.intent!r}, "
            f"forecast_days={self.forecast_days!r}, "
            f"start_day={self.start_day!r}, "
            f"activity={self.activity!r}, "
            f"hypothetical_temperature="
            f"{self.hypothetical_temperature!r}, "
            f"hypothetical_rain_probability="
            f"{self.hypothetical_rain_probability!r}, "
            f"hypothetical_wind_speed="
            f"{self.hypothetical_wind_speed!r}, "
            f"hypothetical_humidity="
            f"{self.hypothetical_humidity!r})"
        )


class QueryParser:
    """Parse weather queries into structured information."""

    INTENT_KEYWORDS = {
        "risk": [
            "risk",
            "dangerous",
            "danger",
            "safe",
            "safety",
            "unsafe",
            "hazard",
            "hazardous",
            "warning",
            "impact",
            "should i",
            "should we",
            "can i",
            "can we",
            "could i",
            "could we",
            "is it safe",
            "is it okay",
            "is it ok",
            "would it be safe",
            "would it be okay",
            "go outside",
            "going outside",
        ],
        "forecast": [
            "forecast",
            "tomorrow",
            "day after tomorrow",
            "next week",
            "this week",
            "later",
            "upcoming",
        ],
        "temperature": [
            "temperature",
            "hot",
            "cold",
            "degree",
            "degrees",
        ],
        "rain": [
            "rain",
            "raining",
            "rainfall",
            "umbrella",
        ],
        "wind": [
            "wind",
            "windy",
            "gust",
        ],
        "humidity": [
            "humidity",
            "humid",
        ],
        "general": [
            "weather",
            "climate",
            "condition",
        ],
    }

    ACTIVITY_KEYWORDS = {
        "running": [
            "run",
            "running",
            "jog",
            "jogging",
        ],
        "walking": [
            "walk",
            "walking",
        ],
        "cycling": [
            "cycle",
            "cycling",
            "bike",
            "biking",
        ],
        "sports": [
            "sport",
            "sports",
            "game",
            "games",
            "football",
            "cricket",
            "badminton",
            "tennis",
        ],
        "travel": [
            "travel",
            "trip",
            "journey",
            "tour",
        ],
        "outdoor_work": [
            "outdoor work",
            "outdoor job",
            "working outside",
            "work outside",
        ],
        "farming": [
            "farm",
            "farming",
            "agriculture",
            "agricultural",
        ],
        "outdoor": [
            "outdoor",
            "outside",
            "go outside",
            "outdoors",
        ],
    }

    # Words that should never remain attached to a location.
    LOCATION_STOP_WORDS = {
        "today",
        "tomorrow",
        "tonight",
        "morning",
        "afternoon",
        "evening",
        "night",
        "later",
        "upcoming",
        "now",
        "this",
        "next",
        "week",
        "weeks",
        "day",
        "days",
        "forecast",
        "weather",
        "temperature",
        "rain",
        "raining",
        "wind",
        "windy",
        "humidity",
        "humid",
        "risk",
        "safe",
        "safety",
        "running",
        "run",
        "walking",
        "walk",
        "cycling",
        "cycle",
        "sports",
        "sport",
        "travel",
        "farming",
        "agriculture",
        "outside",
        "outdoor",
    }

    def parse(
        self,
        question: str,
    ) -> WeatherQuery:
        """Parse a user's weather question."""

        if not question or not question.strip():
            return WeatherQuery()

        normalized = (
            question.lower().strip()
        )

        is_what_if = self._is_what_if(
            normalized
        )

        if is_what_if:
            intent = "what_if"
        else:
            intent = self._extract_intent(
                normalized
            )

        location = self._extract_location(
            question
        )

        forecast_days, start_day = (
            self._extract_forecast_period(
                normalized
            )
        )

        activity = self._extract_activity(
            normalized
        )

        hypothetical_temperature = None
        hypothetical_rain_probability = None
        hypothetical_wind_speed = None
        hypothetical_humidity = None

        if is_what_if:

            hypothetical_temperature = (
                self._extract_temperature(
                    normalized
                )
            )

            hypothetical_rain_probability = (
                self._extract_rain_probability(
                    normalized
                )
            )

            hypothetical_wind_speed = (
                self._extract_wind_speed(
                    normalized
                )
            )

            hypothetical_humidity = (
                self._extract_humidity(
                    normalized
                )
            )

        return WeatherQuery(
            location=location,
            intent=intent,
            forecast_days=forecast_days,
            start_day=start_day,
            activity=activity,
            hypothetical_temperature=(
                hypothetical_temperature
            ),
            hypothetical_rain_probability=(
                hypothetical_rain_probability
            ),
            hypothetical_wind_speed=(
                hypothetical_wind_speed
            ),
            hypothetical_humidity=(
                hypothetical_humidity
            ),
        )

    # ==========================================================
    # INTENT
    # ==========================================================

    def _is_what_if(
        self,
        question: str,
    ) -> bool:
        """Detect hypothetical weather questions."""

        hypothetical_phrases = [
            "what if",
            "what happens if",
            "what would happen if",
            "suppose",
            "assuming",
            "if the temperature",
            "if temperature",
            "if the rain",
            "if rain",
            "if the wind",
            "if wind",
            "if humidity",
            "if the humidity",
        ]

        return any(
            phrase in question
            for phrase in hypothetical_phrases
        )

    def _extract_intent(
        self,
        question: str,
    ) -> str:
        """Determine the user's weather-related intent."""

        risk_keywords = (
            self.INTENT_KEYWORDS["risk"]
        )

        if any(
            keyword in question
            for keyword in risk_keywords
        ):
            return "risk"

        forecast_keywords = (
            self.INTENT_KEYWORDS["forecast"]
        )

        if any(
            keyword in question
            for keyword in forecast_keywords
        ):
            return "forecast"

        for candidate_intent in [
            "temperature",
            "rain",
            "wind",
            "humidity",
            "general",
        ]:
            keywords = (
                self.INTENT_KEYWORDS[
                    candidate_intent
                ]
            )

            if any(
                keyword in question
                for keyword in keywords
            ):
                return candidate_intent

        return "general"

    # ==========================================================
    # ACTIVITY
    # ==========================================================

    def _extract_activity(
        self,
        question: str,
    ) -> str:
        """Determine the activity mentioned."""

        activity_priority = [
            "running",
            "walking",
            "cycling",
            "sports",
            "travel",
            "outdoor_work",
            "farming",
            "outdoor",
        ]

        for activity in activity_priority:

            keywords = (
                self.ACTIVITY_KEYWORDS[
                    activity
                ]
            )

            if any(
                keyword in question
                for keyword in keywords
            ):
                return activity

        return "outdoor"

    # ==========================================================
    # LOCATION
    # ==========================================================

    def _extract_location(
        self,
        question: str,
    ) -> Optional[str]:
        """
        Extract a location from common natural-language patterns.

        Temporal and weather terms are removed from the captured
        location so phrases such as:

            "Guntur tomorrow"

        become:

            "Guntur"
        """

        patterns = [
            r"\bin\s+([A-Za-z][A-Za-z\s,.-]*?)(?=\?|$)",
            r"\bat\s+([A-Za-z][A-Za-z\s,.-]*?)(?=\?|$)",
            r"\bfor\s+([A-Za-z][A-Za-z\s,.-]*?)(?=\?|$)",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                question,
                re.IGNORECASE,
            )

            if not match:
                continue

            location = match.group(1).strip(
                " .,?"
            )

            location = (
                self._clean_location(
                    location
                )
            )

            if location:
                return location

        return None

    def _clean_location(
        self,
        location: str,
    ) -> str:
        """Remove temporal/weather words accidentally captured as location."""

        words = location.split()

        cleaned_words = []

        for word in words:

            normalized_word = (
                word.lower().strip(
                    " .,?"
                )
            )

            if (
                normalized_word
                in self.LOCATION_STOP_WORDS
            ):
                break

            cleaned_words.append(
                word
            )

        cleaned_location = " ".join(
            cleaned_words
        ).strip(
            " .,?"
        )

        return cleaned_location

    # ==========================================================
    # FORECAST PERIOD
    # ==========================================================

    def _extract_forecast_period(
        self,
        question: str,
    ) -> tuple[int, int]:
        """Determine forecast days and starting day."""

        if "day after tomorrow" in question:
            return 1, 2

        if "tomorrow" in question:
            return 1, 1

        if "next week" in question:
            return 7, 1

        if "this week" in question:
            return 7, 0

        match = re.search(
            r"\b(?:for|next)\s+(\d+)\s+days?\b",
            question,
        )

        if match:

            days = int(
                match.group(1)
            )

            days = max(
                1,
                min(days, 7),
            )

            return days, 1

        return 1, 0

    # ==========================================================
    # TEMPERATURE
    # ==========================================================

    def _extract_temperature(
        self,
        question: str,
    ) -> Optional[float]:
        """Extract hypothetical temperature."""

        patterns = [
            (
                r"(?:temperature|temp)"
                r"(?:\s+is|\s+reaches|\s+reached"
                r"|\s+of|\s+at)?"
                r"\s*(-?\d+(?:\.\d+)?)\s*"
                r"(?:°\s*c|degrees?\s*c|c|degrees?)?"
            ),
            (
                r"(-?\d+(?:\.\d+)?)"
                r"\s*°\s*c"
            ),
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                question,
                re.IGNORECASE,
            )

            if match:
                return float(
                    match.group(1)
                )

        return None

    # ==========================================================
    # RAIN
    # ==========================================================

    def _extract_rain_probability(
        self,
        question: str,
    ) -> Optional[float]:
        """Extract hypothetical rain probability."""

        patterns = [
            (
                r"(\d+(?:\.\d+)?)\s*%"
                r"(?:\s+chance)?\s*"
                r"(?:of\s+)?rain"
            ),
            (
                r"(\d+(?:\.\d+)?)\s*percent"
                r"(?:\s+chance)?\s*"
                r"(?:of\s+)?rain"
            ),
            (
                r"(?:chance|probability)"
                r"(?:\s+of)?\s+rain"
                r"(?:\s+is|\s+of)?\s*"
                r"(\d+(?:\.\d+)?)\s*"
                r"(?:%|percent)?"
            ),
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                question,
                re.IGNORECASE,
            )

            if match:

                value = float(
                    match.group(1)
                )

                return max(
                    0.0,
                    min(
                        100.0,
                        value,
                    ),
                )

        return None

    # ==========================================================
    # WIND
    # ==========================================================

    def _extract_wind_speed(
        self,
        question: str,
    ) -> Optional[float]:
        """Extract hypothetical wind speed."""

        patterns = [
            (
                r"(?:wind(?:\s+speed)?|winds?)"
                r"(?:\s+reaches|\s+reached"
                r"|\s+is|\s+of|\s+at)?"
                r"\s*(\d+(?:\.\d+)?)\s*"
                r"(?:km/?h|kmph|kph|mph)?"
            ),
            (
                r"(\d+(?:\.\d+)?)\s*"
                r"(?:km/?h|kmph|kph|mph)"
                r"\s*(?:wind|winds)"
            ),
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                question,
                re.IGNORECASE,
            )

            if match:
                return float(
                    match.group(1)
                )

        return None

    # ==========================================================
    # HUMIDITY
    # ==========================================================

    def _extract_humidity(
        self,
        question: str,
    ) -> Optional[float]:
        """Extract hypothetical humidity."""

        patterns = [
            (
                r"(?:humidity|humid)"
                r"(?:\s+reaches|\s+reached"
                r"|\s+is|\s+of|\s+at)?"
                r"\s*(\d+(?:\.\d+)?)\s*%?"
            ),
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                question,
                re.IGNORECASE,
            )

            if match:

                value = float(
                    match.group(1)
                )

                return max(
                    0.0,
                    min(
                        100.0,
                        value,
                    ),
                )

        return None
