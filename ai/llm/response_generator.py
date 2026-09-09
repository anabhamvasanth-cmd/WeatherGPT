from ai.llm.llm_client import LLMClient
from ai.llm.prompts import WEATHERGPT_SYSTEM_PROMPT


class WeatherResponseGenerator:
    """
    Generate grounded natural-language weather responses.

    The deterministic WeatherGPT engines calculate weather risk,
    confidence, and activity decisions.

    Gemini is used only to explain those calculated results.
    """

    def __init__(self):
        self.llm = None

        try:
            self.llm = LLMClient()
        except Exception:
            self.llm = None

    def generate_response(
        self,
        user_question: str,
        weather_context: str,
    ) -> str:
        """
        Generate a response using the user's question and
        verified WeatherGPT context.

        Gemini is attempted first. If Gemini is unavailable,
        the deterministic formatter provides the response.
        """

        user_prompt = self._build_user_prompt(
            user_question=user_question,
            weather_context=weather_context,
        )

        if self.llm is not None:
            try:
                return self.llm.generate(
                    system_prompt=WEATHERGPT_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                )
            except Exception:
                # Gemini may be unavailable because of quota,
                # connectivity, or another temporary API issue.
                # The deterministic analysis remains available.
                pass

        return self._deterministic_response(
            user_question=user_question,
            weather_context=weather_context,
        )

    @staticmethod
    def _build_user_prompt(
        user_question: str,
        weather_context: str,
    ) -> str:
        """
        Build the grounded prompt supplied to Gemini.
        """

        return f"""
USER QUESTION:
{user_question}

VERIFIED WEATHERGPT CONTEXT:
{weather_context}

INSTRUCTIONS:

Answer the user's question using the verified context above.

The weather data, Forecast Confidence, Risk Engine,
What-If Engine, and Decision Engine are authoritative.

Do not invent missing information.

Preserve all calculated:
- weather values
- confidence values
- risk levels
- risk scores
- impacts
- decisions
- recommendations

If the context contains a hypothetical scenario, clearly
identify it as hypothetical.

Answer directly and concisely.
"""

    def _deterministic_response(
        self,
        user_question: str,
        weather_context: str,
    ) -> str:
        """
        Produce a clean user-facing response without Gemini.

        This deliberately exposes only authoritative WeatherGPT
        information and omits internal RAG retrieval content.
        """

        lines = [
            line.strip()
            for line in weather_context.splitlines()
            if line.strip()
        ]

        output = []
        section = None

        for line in lines:
            lower = line.lower()

            # --------------------------------------------------
            # Ignore internal metadata
            # --------------------------------------------------

            if lower.startswith("language:"):
                continue

            if lower.startswith("response language:"):
                continue

            # --------------------------------------------------
            # Ignore RAG retrieval / internal scoring
            # --------------------------------------------------

            if lower.startswith("score:"):
                continue

            if lower.startswith("[0."):
                continue

            # --------------------------------------------------
            # Forecast
            # --------------------------------------------------

            if lower.startswith("forecast for"):
                section = "forecast"
                output.append(line)
                continue

            if section == "forecast":
                if len(line) >= 4 and line[:4].isdigit():
                    output.append(line)
                    continue

            # --------------------------------------------------
            # Forecast confidence
            # --------------------------------------------------

            if lower.startswith("forecast confidence"):
                section = "confidence"
                output.append(line)
                continue

            # --------------------------------------------------
            # Hypothetical / What-If
            # --------------------------------------------------

            if lower.startswith("hypothetical weather scenario"):
                section = "what_if"
                output.append(line)
                continue

            if lower.startswith("hypothetical "):
                output.append(line)
                continue

            # --------------------------------------------------
            # Risk assessment
            # --------------------------------------------------

            if lower.startswith("risk assessment"):
                section = "risk"
                output.append(line)
                continue

            if lower.startswith("overall risk:"):
                output.append(line)
                continue

            if lower.startswith("risk score:"):
                output.append(line)
                continue

            if lower.startswith("heat impact:"):
                output.append(line)
                continue

            if lower.startswith("rain impact:"):
                output.append(line)
                continue

            if lower.startswith("wind impact:"):
                output.append(line)
                continue

            if lower.startswith("humidity impact:"):
                output.append(line)
                continue

            # --------------------------------------------------
            # Decision
            # --------------------------------------------------

            if lower == "decision:":
                section = "decision"
                output.append(line)
                continue

            if lower.startswith("decision:"):
                output.append(line)
                continue

            # --------------------------------------------------
            # Recommendation
            # --------------------------------------------------

            if lower == "recommendation:":
                section = "recommendation"
                output.append(line)
                continue

            if lower.startswith("recommendation:"):
                output.append(line)
                continue

            if section == "recommendation" and line.startswith("- "):
                output.append(line)
                continue

            # --------------------------------------------------
            # Risk recommendations
            # --------------------------------------------------

            if lower == "risk recommendations:":
                section = "risk_recommendations"
                output.append(line)
                continue

            if (
                section == "risk_recommendations"
                and line.startswith("- ")
            ):
                output.append(line)
                continue

        # ------------------------------------------------------
        # Remove duplicates while preserving order
        # ------------------------------------------------------

        cleaned = []
        seen = set()

        for line in output:
            normalized = line.lower().strip()

            if normalized in seen:
                continue

            seen.add(normalized)
            cleaned.append(line)

        # ------------------------------------------------------
        # Empty result
        # ------------------------------------------------------

        if not cleaned:
            return (
                "WeatherGPT could not generate a response "
                "from the available verified weather data."
            )

        # ------------------------------------------------------
        # Final response
        # ------------------------------------------------------

        response = [
            "WeatherGPT Analysis",
            "",
        ]

        response.extend(cleaned)

        response.extend(
            [
                "",
                "Note: WeatherGPT's weather risk and activity "
                "decision are calculated by its deterministic "
                "analysis engines.",
            ]
        )

        return "\n".join(response)
