import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()


class LLMClient:
    """Client responsible for communicating with Google Gemini."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured. "
                "Add it to the .env file."
            )

        self.client = genai.Client(api_key=api_key)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "gemini-3.6-flash",
    ) -> str:
        """Generate a response from Gemini with controlled retry handling."""

        max_attempts = 4
        delays = [2, 5, 10]

        for attempt in range(max_attempts):
            try:
                chat = self.client.chats.create(
                    model=model,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                    ),
                )

                response = chat.send_message(
                    message=user_prompt,
                )

                if not response.text:
                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                return response.text.strip()

            except Exception as error:
                error_text = str(error)

                is_quota_error = (
                    "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                    or "quota" in error_text.lower()
                )

                if is_quota_error:
                    raise RuntimeError(
                        "Gemini API quota has been exhausted. "
                        "The deterministic WeatherGPT analysis is "
                        "still available, but natural-language "
                        "generation through Gemini is temporarily "
                        "unavailable."
                    ) from error

                is_temporary_error = (
                    "503" in error_text
                    or "UNAVAILABLE" in error_text
                )

                if not is_temporary_error:
                    raise

                if attempt == max_attempts - 1:
                    raise RuntimeError(
                        "Gemini is temporarily unavailable after "
                        f"{max_attempts} attempts. Please try again later."
                    ) from error

                delay = delays[attempt]

                print(
                    "Gemini request temporarily unavailable. "
                    f"Retrying in {delay} seconds..."
                )

                time.sleep(delay)
