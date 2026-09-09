class ForecastConfidence:
    """Estimate confidence in a weather forecast."""

    def calculate(
        self,
        precipitation_probability: float | None = None,
        forecast_days: int = 1,
    ) -> float:
        """
        Calculate a confidence score between 0 and 1.

        Confidence decreases as the forecast gets further into the
        future. Uncertain precipitation probabilities also reduce
        confidence.
        """

        if forecast_days < 1:
            forecast_days = 1

        confidence = max(
            0.5,
            1.0 - ((forecast_days - 1) * 0.08),
        )

        if precipitation_probability is not None:
            uncertainty = abs(precipitation_probability - 50) / 50
            confidence *= 0.75 + (0.25 * uncertainty)

        return round(
            max(0.0, min(1.0, confidence)),
            2,
        )
