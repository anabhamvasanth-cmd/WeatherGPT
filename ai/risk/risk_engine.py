from ai.risk.impact import WeatherImpact


class RiskEngine:
    """Evaluate overall weather-related risk."""

    RISK_SCORES = {
        "minimal": 0,
        "low": 1,
        "moderate": 2,
        "high": 3,
        "extreme": 4,
    }

    def __init__(self):
        self.impact_analyzer = WeatherImpact()

    def assess(
        self,
        temperature: float | None = None,
        precipitation_probability: float | None = None,
        wind_speed: float | None = None,
        humidity: float | None = None,
    ) -> dict:
        """Generate an overall weather risk assessment."""

        impacts = self.impact_analyzer.assess(
            temperature=temperature,
            precipitation_probability=precipitation_probability,
            wind_speed=wind_speed,
            humidity=humidity,
        )

        if not impacts:
            return {
                "overall_risk": "unknown",
                "score": 0,
                "impacts": {},
                "recommendations": [],
            }

        scores = [
            self.RISK_SCORES.get(level, 0)
            for level in impacts.values()
        ]

        highest_score = max(scores)

        if highest_score >= 4:
            overall_risk = "extreme"
        elif highest_score >= 3:
            overall_risk = "high"
        elif highest_score >= 2:
            overall_risk = "moderate"
        elif highest_score >= 1:
            overall_risk = "low"
        else:
            overall_risk = "minimal"

        recommendations = self._generate_recommendations(
            impacts
        )

        return {
            "overall_risk": overall_risk,
            "score": highest_score,
            "impacts": impacts,
            "recommendations": recommendations,
        }

    def _generate_recommendations(
        self,
        impacts: dict,
    ) -> list[str]:
        """Generate practical recommendations."""

        recommendations = []

        heat = impacts.get("heat")

        if heat == "extreme":
            recommendations.append(
                "Avoid prolonged outdoor exposure and seek a cool environment."
            )
        elif heat == "high":
            recommendations.append(
                "Stay hydrated and limit prolonged outdoor exposure."
            )
        elif heat == "moderate":
            recommendations.append(
                "Stay hydrated when spending extended time outdoors."
            )

        rain = impacts.get("rain")

        if rain == "high":
            recommendations.append(
                "Carry rain protection and consider delaying outdoor activities."
            )
        elif rain == "moderate":
            recommendations.append(
                "Carry an umbrella or raincoat when going outdoors."
            )
        elif rain == "low":
            recommendations.append(
                "Consider carrying light rain protection."
            )

        wind = impacts.get("wind")

        if wind == "extreme":
            recommendations.append(
                "Avoid exposed outdoor areas because of strong winds."
            )
        elif wind == "high":
            recommendations.append(
                "Use caution in exposed areas because of strong winds."
            )
        elif wind == "moderate":
            recommendations.append(
                "Be cautious around exposed or unsecured objects."
            )

        humidity = impacts.get("humidity")

        if humidity == "high":
            recommendations.append(
                "Expect humid conditions and stay hydrated."
            )

        return recommendations
