class ForecastFusion:
    """Combine weather observations from multiple sources."""

    def combine(self, forecasts: list[dict]) -> dict:
        """
        Combine multiple forecast dictionaries.

        Numeric values are averaged.
        Non-numeric values use the first available value.
        """

        if not forecasts:
            return {}

        result = {}

        keys = set()

        for forecast in forecasts:
            keys.update(forecast.keys())

        for key in keys:
            values = [
                forecast[key]
                for forecast in forecasts
                if key in forecast and forecast[key] is not None
            ]

            if not values:
                continue

            numeric_values = [
                value
                for value in values
                if isinstance(value, (int, float))
            ]

            if len(numeric_values) == len(values):
                result[key] = round(
                    sum(numeric_values) / len(numeric_values),
                    2,
                )
            else:
                result[key] = values[0]

        return result
