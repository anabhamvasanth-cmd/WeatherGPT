class WeatherImpact:
    """Estimate practical impacts of weather conditions."""

    def assess(
        self,
        temperature: float | None = None,
        precipitation_probability: float | None = None,
        wind_speed: float | None = None,
        humidity: float | None = None,
    ) -> dict:
        """Assess potential impacts from weather conditions."""

        impacts = {}

        if temperature is not None:
            if temperature >= 40:
                impacts["heat"] = "extreme"
            elif temperature >= 35:
                impacts["heat"] = "high"
            elif temperature >= 30:
                impacts["heat"] = "moderate"
            else:
                impacts["heat"] = "low"

        if precipitation_probability is not None:
            if precipitation_probability >= 80:
                impacts["rain"] = "high"
            elif precipitation_probability >= 50:
                impacts["rain"] = "moderate"
            elif precipitation_probability >= 30:
                impacts["rain"] = "low"
            else:
                impacts["rain"] = "minimal"

        if wind_speed is not None:
            if wind_speed >= 50:
                impacts["wind"] = "extreme"
            elif wind_speed >= 30:
                impacts["wind"] = "high"
            elif wind_speed >= 15:
                impacts["wind"] = "moderate"
            else:
                impacts["wind"] = "low"

        if humidity is not None:
            if humidity >= 80:
                impacts["humidity"] = "high"
            elif humidity >= 60:
                impacts["humidity"] = "moderate"
            else:
                impacts["humidity"] = "low"

        return impacts
