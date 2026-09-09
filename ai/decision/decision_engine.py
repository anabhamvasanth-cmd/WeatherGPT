class DecisionEngine:
    """Convert weather risk assessments into activity-aware decisions."""

    SUPPORTED_ACTIVITIES = {
        "outdoor",
        "walking",
        "running",
        "cycling",
        "sports",
        "travel",
        "outdoor_work",
        "farming",
    }

    def evaluate(
        self,
        risk_assessment: dict,
        activity: str = "outdoor",
    ) -> dict:
        """
        Evaluate an activity based on the calculated weather risk.

        The decision engine does not modify the Risk Engine's calculated
        risk level. It only converts that risk into an activity-specific
        recommendation.
        """

        activity = self._normalize_activity(activity)

        overall_risk = risk_assessment.get(
            "overall_risk",
            "unknown",
        )

        impacts = risk_assessment.get(
            "impacts",
            {},
        )

        if overall_risk == "unknown":
            decision = "insufficient_data"
            recommendation = (
                "There is not enough weather risk information "
                "to make a reliable decision."
            )

        elif activity in {"running", "cycling", "sports"}:
            decision, recommendation = self._evaluate_active_outdoor_activity(
                overall_risk,
                impacts,
            )

        elif activity == "outdoor_work":
            decision, recommendation = self._evaluate_outdoor_work(
                overall_risk,
                impacts,
            )

        elif activity == "farming":
            decision, recommendation = self._evaluate_farming(
                overall_risk,
                impacts,
            )

        elif activity == "travel":
            decision, recommendation = self._evaluate_travel(
                overall_risk,
                impacts,
            )

        elif activity == "walking":
            decision, recommendation = self._evaluate_walking(
                overall_risk,
                impacts,
            )

        else:
            decision, recommendation = self._evaluate_general_outdoor(
                overall_risk,
                impacts,
            )

        return {
            "activity": activity,
            "risk_level": overall_risk,
            "decision": decision,
            "recommendation": recommendation,
        }

    def _normalize_activity(self, activity: str) -> str:
        """Normalize common activity names."""

        activity = activity.lower().strip()

        aliases = {
            "walk": "walking",
            "jogging": "running",
            "run": "running",
            "bike": "cycling",
            "biking": "cycling",
            "cycle": "cycling",
            "cycling": "cycling",
            "sport": "sports",
            "game": "sports",
            "games": "sports",
            "outdoor work": "outdoor_work",
            "outdoor job": "outdoor_work",
            "farm": "farming",
            "agriculture": "farming",
            "trip": "travel",
            "journey": "travel",
        }

        return aliases.get(
            activity,
            activity
            if activity in self.SUPPORTED_ACTIVITIES
            else "outdoor",
        )

    def _evaluate_general_outdoor(
        self,
        risk_level: str,
        impacts: dict,
    ) -> tuple[str, str]:
        """Evaluate general outdoor activity."""

        if risk_level == "extreme":
            return (
                "avoid",
                "Avoid the outdoor activity under the current weather risk.",
            )

        if risk_level == "high":
            return (
                "caution",
                "Use caution and consider postponing the outdoor activity "
                "if possible.",
            )

        if risk_level == "moderate":
            return (
                "caution",
                "The outdoor activity can be considered with appropriate "
                "precautions.",
            )

        if risk_level == "low":
            return (
                "proceed",
                "The weather risk is relatively low. "
                "Normal precautions are recommended.",
            )

        return (
            "proceed",
            "The weather risk is minimal. "
            "Normal precautions are recommended.",
        )

    def _evaluate_active_outdoor_activity(
        self,
        risk_level: str,
        impacts: dict,
    ) -> tuple[str, str]:
        """Evaluate running, cycling, and outdoor sports."""

        heat = impacts.get("heat")
        rain = impacts.get("rain")
        wind = impacts.get("wind")

        if risk_level == "extreme":
            return (
                "avoid",
                "Avoid strenuous outdoor activity under the current "
                "weather risk.",
            )

        if heat == "extreme":
            return (
                "avoid",
                "Avoid strenuous outdoor activity because of the "
                "extreme heat impact.",
            )

        if risk_level == "high":
            return (
                "postpone",
                "Consider postponing strenuous outdoor activity "
                "because the overall weather risk is high.",
            )

        if rain == "high":
            return (
                "postpone",
                "Consider postponing the activity because of the "
                "high rain impact.",
            )

        if wind == "high":
            return (
                "caution",
                "Use caution during the activity because of the "
                "high wind impact.",
            )

        if risk_level == "moderate":
            return (
                "caution",
                "The activity can be considered with appropriate "
                "precautions and attention to changing conditions.",
            )

        return (
            "proceed",
            "The weather risk is relatively low for the activity. "
            "Normal precautions are recommended.",
        )

    def _evaluate_outdoor_work(
        self,
        risk_level: str,
        impacts: dict,
    ) -> tuple[str, str]:
        """Evaluate outdoor work."""

        heat = impacts.get("heat")

        if risk_level == "extreme":
            return (
                "avoid",
                "Avoid prolonged outdoor work under the current "
                "weather risk.",
            )

        if heat == "extreme":
            return (
                "avoid",
                "Avoid prolonged outdoor work because of the "
                "extreme heat impact.",
            )

        if risk_level == "high":
            return (
                "caution",
                "Use caution and consider reducing or postponing "
                "prolonged outdoor work.",
            )

        if risk_level == "moderate":
            return (
                "caution",
                "Outdoor work can be considered with appropriate "
                "precautions and breaks.",
            )

        return (
            "proceed",
            "Outdoor work can generally proceed with normal precautions.",
        )

    def _evaluate_farming(
        self,
        risk_level: str,
        impacts: dict,
    ) -> tuple[str, str]:
        """Evaluate farming or agricultural activity."""

        rain = impacts.get("rain")
        wind = impacts.get("wind")

        if risk_level == "extreme":
            return (
                "avoid",
                "Consider postponing non-essential outdoor farming "
                "activities under the current weather risk.",
            )

        if rain == "high":
            return (
                "caution",
                "Consider delaying weather-sensitive farming activities "
                "because of the high rain impact.",
            )

        if wind == "high":
            return (
                "caution",
                "Use caution with exposed farming activities because "
                "of the high wind impact.",
            )

        if risk_level == "high":
            return (
                "caution",
                "Use caution and consider adjusting weather-sensitive "
                "farming activities.",
            )

        if risk_level == "moderate":
            return (
                "caution",
                "Farming activities can be considered with appropriate "
                "precautions.",
            )

        return (
            "proceed",
            "Weather risk is relatively low for farming activities. "
            "Normal precautions are recommended.",
        )

    def _evaluate_travel(
        self,
        risk_level: str,
        impacts: dict,
    ) -> tuple[str, str]:
        """Evaluate travel."""

        rain = impacts.get("rain")
        wind = impacts.get("wind")

        if risk_level == "extreme":
            return (
                "avoid",
                "Consider postponing non-essential travel under the "
                "current weather risk.",
            )

        if rain == "high" or wind == "high":
            return (
                "caution",
                "Travel may require additional caution because of "
                "the current weather impacts.",
            )

        if risk_level == "high":
            return (
                "caution",
                "Travel can involve increased weather-related risk. "
                "Check conditions before departure.",
            )

        if risk_level == "moderate":
            return (
                "caution",
                "Travel can be considered with normal weather "
                "precautions.",
            )

        return (
            "proceed",
            "Weather risk is relatively low for travel. "
            "Normal precautions are recommended.",
        )

    def _evaluate_walking(
        self,
        risk_level: str,
        impacts: dict,
    ) -> tuple[str, str]:
        """Evaluate walking."""

        if risk_level == "extreme":
            return (
                "avoid",
                "Avoid the walk under the current weather risk.",
            )

        if risk_level == "high":
            return (
                "caution",
                "Consider postponing the walk or keeping it brief "
                "because the overall weather risk is high.",
            )

        if risk_level == "moderate":
            return (
                "caution",
                "Walking can be considered with appropriate "
                "precautions.",
            )

        return (
            "proceed",
            "Walking can generally proceed with normal precautions.",
        )
