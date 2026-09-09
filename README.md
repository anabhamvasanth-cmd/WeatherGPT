# WeatherGPT

AI-powered conversational weather forecasting, risk analysis, alerts, and personalized weather guidance.

## Project Overview

WeatherGPT is an AI-powered conversational platform that provides:

- Real-time weather information
- Weather forecasting
- Risk analysis
- Personalized weather recommendations
- Severe weather alerts
- What-if scenario analysis
- Multilingual interaction
- Voice-based interaction
- Map-based weather information

## Project Architecture

User
↓
NLP / Voice
↓
AI Weather Engine
↓
Weather Data + ML Models
↓
Risk & Decision Engine
↓
LLM + RAG
↓
Personalized Response
↓
Flutter Application

## Technology Stack

### AI / ML
- Python
- XGBoost
- LLM
- RAG
- NLP
- Speech-to-Text
- Text-to-Speech

### Backend
- FastAPI
- REST APIs

### Mobile
- Flutter

### Database
- PostgreSQL
- PostGIS

### Weather Data
- IMD
- GFS / WRF
- Radar
- Satellite data

## Team Branches

| Branch | Responsibility |
|---|---|
| `main` | Stable integrated code |
| `member1-ml` | Weather data and ML |
| `member2-backend` | Backend, risk and decision engine |
| `member3-ai` | LLM, RAG, NLP, voice and languages |
| `member4-flutter` | Flutter application and GIS |

## Development Workflow

Each member works on their own branch.

```text
Feature Development
        ↓
Member Branch
        ↓
Pull Request
        ↓
Code Review
        ↓
Testing
        ↓
Merge into main