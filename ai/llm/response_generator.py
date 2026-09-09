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

        user_prompt = f"""
User question:
{user_question}

Verified weather information:
{weather_context}

Using only the supplied weather information, answer the user's
question and provide a practical recommendation when appropriate.
"""

        return self.llm.generate(
            system_prompt=WEATHERGPT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
