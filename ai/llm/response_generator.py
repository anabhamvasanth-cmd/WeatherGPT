from ai.llm.llm_client import LLMClient
from ai.llm.prompts import WEATHERGPT_SYSTEM_PROMPT


class WeatherResponseGenerator:
    """Generate natural-language weather responses."""

    def __init__(self):
        self.llm = LLMClient()

    def generate_response(
        self,
        user_question: str,
        weather_context: str,
    ) -> str:
        """Generate a response using Gemini with deterministic fallback."""

        user_prompt = f"""
User question:
{user_question}

AUTHORITATIVE WEATHER AND DECISION INFORMATION:
The following information comes directly from WeatherGPT's
weather data, Risk Engine, Forecast Confidence module,
What-If Engine, and Decision Engine.

{weather_context}

IMPORTANT:
The calculated Risk Engine and Decision Engine results are authoritative.

RETRIEVED DOMAIN KNOWLEDGE:
The retrieved knowledge is supporting information only. It may explain
the meaning or practical implications of the calculated result, but it
must never override or change the calculated risk level or decision.

Using the information above, answer the user's question clearly and
concisely.

Do not invent weather values.
Do not invent risk levels.
Do not invent decisions.
Do not change calculated risk levels or decisions.
"""

        try:
            return self.llm.generate(
                system_prompt=WEATHERGPT_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

        except RuntimeError:
            return self._fallback_response(
                user_question=user_question,
                weather_context=weather_context,
            )

    def _fallback_response(
        self,
        user_question: str,
        weather_context: str,
    ) -> str:
        """Generate a deterministic response when Gemini is unavailable."""

        lines = [
            "WeatherGPT Analysis",
            "",
            "Based on the verified weather information:",
            "",
        ]

        context_lines = [
            line.strip()
            for line in weather_context.splitlines()
            if line.strip()
        ]

        skip_prefixes = (
            "Intent:",
            "Forecast days:",
            "Start day:",
            "Activity:",
        )

        for line in context_lines:
            if not line.startswith(skip_prefixes):
                lines.append(f"- {line}")

        lines.extend(
            [
                "",
                "Note: Natural-language generation through Gemini "
                "is temporarily unavailable. "
                "The weather data and deterministic WeatherGPT "
                "analysis above remain available.",
            ]
        )

        return "\n".join(lines)
