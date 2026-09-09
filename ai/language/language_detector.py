from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException


DetectorFactory.seed = 0


class LanguageDetector:
    """Detect the language of a user query."""

    SUPPORTED_LANGUAGES = {
        "en": "English",
        "hi": "Hindi",
        "te": "Telugu",
        "ta": "Tamil",
        "kn": "Kannada",
        "ml": "Malayalam",
        "bn": "Bengali",
        "mr": "Marathi",
    }

    def detect_language(self, text: str) -> dict:
        """Detect and return language information."""

        if not text or not text.strip():
            return {
                "code": "en",
                "name": "English",
                "supported": True,
            }

        try:
            language_code = detect(text)

        except LangDetectException:
            language_code = "en"

        language_name = self.SUPPORTED_LANGUAGES.get(
            language_code,
            "English",
        )

        return {
            "code": language_code,
            "name": language_name,
            "supported": language_code in self.SUPPORTED_LANGUAGES,
        }
