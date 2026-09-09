from typing import Any

import httpx
from cachetools import TTLCache
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ai.alerts.alert_engine import WeatherAlertEngine
from ai.best_time.best_time_engine import BestTimeEngine
from ai.orchestrator.chat_service import ChatService


app = FastAPI(
    title="WeatherGPT Backend",
    description="AI-powered weather decision-support backend",
    version="1.2.0",
)


# ============================================================================
# CORS
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# CACHE
# ============================================================================

cache = TTLCache(
    maxsize=100,
    ttl=300,
)

current_weather_cache = TTLCache(
    maxsize=100,
    ttl=300,
)


# ============================================================================
# AI SERVICE
# ============================================================================

try:
    chat_service = ChatService()

except Exception as error:
    chat_service = None
    chat_service_error = error

else:
    chat_service_error = None


# ============================================================================
# ALERT SERVICE
# ============================================================================

try:
    alert_engine = WeatherAlertEngine()

except Exception as error:
    alert_engine = None
    alert_engine_error = error

else:
    alert_engine_error = None


# ============================================================================
# BEST TIME SERVICE
# ============================================================================

try:
    best_time_engine = BestTimeEngine()

except Exception as error:
    best_time_engine = None
    best_time_engine_error = error

else:
    best_time_engine_error = None


# ============================================================================
# MODELS
# ============================================================================

class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural-language weather question",
    )


class ChatResponse(BaseModel):
    question: str
    answer: str
    cached: bool = False


class HealthResponse(BaseModel):
    status: str
    ai_service: str


# ============================================================================
# WEATHER HELPERS
# ============================================================================

def weather_condition(
    weather_code: int,
) -> str:

    conditions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }

    return conditions.get(
        weather_code,
        "Unknown",
    )


async def get_coordinates(
    location: str,
) -> tuple[float, float, str]:

    geocoding_url = (
        "https://geocoding-api.open-meteo.com/v1/search"
    )

    async with httpx.AsyncClient(
        timeout=10.0,
    ) as client:

        response = await client.get(
            geocoding_url,
            params={
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json",
            },
        )

    response.raise_for_status()

    data = response.json()

    results = data.get(
        "results",
        [],
    )

    if not results:
        raise ValueError(
            f"Location '{location}' was not found."
        )

    result = results[0]

    name = result.get(
        "name",
        location,
    )

    latitude = result["latitude"]
    longitude = result["longitude"]

    return (
        latitude,
        longitude,
        name,
    )


async def get_current_weather(
    location: str,
) -> dict[str, Any]:

    cache_key = location.strip().lower()

    if cache_key in current_weather_cache:
        return current_weather_cache[cache_key]

    (
        latitude,
        longitude,
        resolved_location,
    ) = await get_coordinates(
        location,
    )

    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
    )

    async with httpx.AsyncClient(
        timeout=10.0,
    ) as client:

        response = await client.get(
            weather_url,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "precipitation,"
                    "weather_code,"
                    "wind_speed_10m"
                ),
                "timezone": "auto",
            },
        )

    response.raise_for_status()

    data = response.json()

    current = data.get(
        "current",
        {},
    )

    result = {
        "location": resolved_location,
        "time": current.get("time"),
        "temperature": current.get(
            "temperature_2m",
        ),
        "feels_like": current.get(
            "apparent_temperature",
        ),
        "humidity": current.get(
            "relative_humidity_2m",
        ),
        "precipitation": current.get(
            "precipitation",
        ),
        "wind_speed": current.get(
            "wind_speed_10m",
        ),
        "weather_code": current.get(
            "weather_code",
        ),
        "condition": weather_condition(
            int(
                current.get(
                    "weather_code",
                    0,
                )
            )
        ),
        "timezone": data.get(
            "timezone",
        ),
        "source": "Open-Meteo",
    }

    current_weather_cache[cache_key] = result

    return result


# ============================================================================
# ROOT
# ============================================================================

@app.get("/")
async def root() -> dict[str, str]:

    return {
        "message": "WeatherGPT API is running!",
        "version": "1.2.0",
    }


# ============================================================================
# HEALTH
# ============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
)
async def health() -> HealthResponse:

    if chat_service is None:
        return HealthResponse(
            status="degraded",
            ai_service="unavailable",
        )

    return HealthResponse(
        status="healthy",
        ai_service="available",
    )


# ============================================================================
# CURRENT WEATHER
# ============================================================================

@app.get("/current")
async def current_weather(
    location: str = "Guntur",
) -> dict[str, Any]:

    try:
        return await get_current_weather(
            location,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to retrieve current weather: "
                f"{error}"
            ),
        ) from error


# ============================================================================
# WEATHER ALERTS
# ============================================================================

@app.get("/alerts")
def weather_alerts(
    location: str = "Guntur",
    days: int = 3,
) -> dict[str, Any]:

    if alert_engine is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "WeatherGPT alert engine could not "
                "be initialized. "
                f"Error: {alert_engine_error}"
            ),
        )

    location = location.strip()

    if not location:
        raise HTTPException(
            status_code=400,
            detail="Location cannot be empty.",
        )

    if days < 1 or days > 7:
        raise HTTPException(
            status_code=400,
            detail=(
                "Alert forecast days must be "
                "between 1 and 7."
            ),
        )

    try:

        return alert_engine.generate_alerts(
            location=location,
            days=days,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to generate weather alerts. "
                f"Error: {error}"
            ),
        ) from error


# ============================================================================
# BEST TIME + BACKUP PLAN
# ============================================================================

@app.get("/best-time")
def best_time(
    location: str = "Guntur",
    activity: str = "outdoor",
    days: int = 1,
    start_day: int = 0,
) -> dict[str, Any]:

    if best_time_engine is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "WeatherGPT best-time engine could not "
                "be initialized. "
                f"Error: {best_time_engine_error}"
            ),
        )

    location = location.strip()
    activity = activity.strip()

    if not location:
        raise HTTPException(
            status_code=400,
            detail="Location cannot be empty.",
        )

    if not activity:
        activity = "outdoor"

    if days < 1 or days > 7:
        raise HTTPException(
            status_code=400,
            detail="Best-time forecast days must be between 1 and 7.",
        )

    if start_day < 0 or start_day > 6:
        raise HTTPException(
            status_code=400,
            detail="Best-time start day must be between 0 and 6.",
        )

    try:
        return best_time_engine.generate_plan(
            location=location,
            activity=activity,
            days=days,
            start_day=start_day,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to generate the best-time plan. "
                f"Error: {error}"
            ),
        ) from error


# ============================================================================
# CHAT
# ============================================================================

@app.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
) -> ChatResponse:

    if chat_service is None:

        raise HTTPException(
            status_code=503,
            detail=(
                "WeatherGPT AI service could not "
                "be initialized. "
                f"Error: {chat_service_error}"
            ),
        )

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    cache_key = question.lower()

    if cache_key in cache:

        return ChatResponse(
            question=question,
            answer=cache[cache_key],
            cached=True,
        )

    try:

        answer = chat_service.process(
            question,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "WeatherGPT could not process "
                "the request. "
                f"Error: {error}"
            ),
        ) from error

    if not isinstance(
        answer,
        str,
    ):
        answer = str(answer)

    cache[cache_key] = answer

    return ChatResponse(
        question=question,
        answer=answer,
        cached=False,
    )


# ============================================================================
# CACHE STATUS
# ============================================================================

@app.get("/cache")
async def cache_status() -> dict[str, Any]:

    return {
        "chat_cache_size": len(cache),
        "weather_cache_size": len(
            current_weather_cache
        ),
        "max_size": cache.maxsize,
        "ttl_seconds": 300,
    }


# ============================================================================
# CLEAR CACHE
# ============================================================================

@app.delete("/cache")
async def clear_cache() -> dict[str, Any]:

    cache.clear()
    current_weather_cache.clear()

    return {
        "message": "WeatherGPT caches cleared.",
        "chat_cache_size": 0,
        "weather_cache_size": 0,
    }
