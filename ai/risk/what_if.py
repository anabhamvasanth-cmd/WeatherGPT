from ai.risk.risk_engine import RiskEngine


class WeatherWhatIf:
    """Perform hypothetical weather risk analysis."""

    def __init__(self):
        self.risk_engine = RiskEngine()

    def analyze(
        self,
        temperature: float | None = None,
        precipitation_probability: float | None = None,
        wind_speed: float | None = None,
        humidity: float | None = None,
    ) -> dict:
        """
        Analyze a hypothetical weather scenario.

        The supplied values represent the hypothetical conditions.
        """

        risk = self.risk_engine.assess(
            temperature=temperature,
            precipitation_probability=precipitation_probability,
            wind_speed=wind_speed,
            humidity=humidity,
        )

        return {
            "scenario": {
                "temperature": temperature,
                "precipitation_probability": precipitation_probability,
                "wind_speed": wind_speed,
                "humidity": humidity,
            },
            "risk_assessment": risk,
        }
