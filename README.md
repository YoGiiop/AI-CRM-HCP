# AI-First CRM HCP Module

This repository contains a split-screen HCP interaction logging experience built for the technical assessment brief. The left panel is a readonly CRM interaction form. The right panel is an AI assistant chat that drives all form updates through LangGraph tools and Groq-hosted LLM calls.

## Tech Stack

- Frontend: React, Redux Toolkit, Create React App
- Backend: FastAPI, SQLAlchemy
- AI agent framework: LangGraph
- LLM provider: Groq
- Primary extraction model: `llama-3.1-8b-instant`
- Routing model: `llama-3.3-70b-versatile`
- Automatic fallback model: `llama-3.3-70b-versatile` if the primary model is unavailable on the active Groq account
- Database: MySQL or PostgreSQL via `DATABASE_URL`

## Assessment Alignment

The implementation follows the key constraints from the prompt:

- Split-screen layout that mirrors the provided interaction logging screen
- Left-side form is populated by the AI assistant only
- Chat-first interaction model for logging and editing HCP data
- LangGraph-based agent flow with more than five tools
- Groq-backed LLM integration, with `llama-3.1-8b-instant` used for structured extraction

Note: `gemma2-9b-it` is deprecated on Groq. The app now uses `llama-3.1-8b-instant` as the primary structured-extraction model and automatically falls back to `llama-3.3-70b-versatile` if needed.

## LangGraph Tools

The backend agent supports these tools:

1. `log_interaction`
2. `edit_interaction`
3. `suggest_followup`
4. `summarize_interaction`
5. `generate_insight`
6. `search_interactions`

Each tool is selected through LangGraph routing and returns a structured payload that the frontend renders in the assistant panel.

## Project Structure

- [backend/app/main.py](backend/app/main.py): FastAPI entrypoint and persistence logic
- [backend/app/agents/langgraph_agent.py](backend/app/agents/langgraph_agent.py): LangGraph router and tool nodes
- [backend/app/agents/tools.py](backend/app/agents/tools.py): Tool implementations
- [backend/app/agents/llm.py](backend/app/agents/llm.py): Groq LLM helpers and datetime normalization
- [frontend/src/components/Form.js](frontend/src/components/Form.js): readonly HCP interaction screen
- [frontend/src/components/Chat.js](frontend/src/components/Chat.js): AI assistant panel and chat orchestration

## Environment Setup

### Backend

Create `backend/.env` with the required values:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_PRIMARY_MODEL=llama-3.1-8b-instant
GROQ_ROUTING_MODEL=llama-3.3-70b-versatile
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/ai_crm
FRONTEND_ORIGIN=http://localhost:3000
```

Install dependencies in the backend environment, then run:

```bash
uvicorn app.main:app --reload
```

### Frontend

Inside `frontend`, install packages and start the app:

```bash
npm install
npm start
```

Optional frontend environment variable:

```env
REACT_APP_API_URL=http://127.0.0.1:8000
```

## Example Prompts

Use the assistant panel with prompts such as:

- `Today I met with Dr. Smith and discussed Product X efficacy. The sentiment was positive and I shared brochures.`
- `Actually, the name was Dr. John and the sentiment was negative.`
- `Suggest next best actions for this interaction.`
- `Summarize this interaction for CRM.`
- `Give me the commercial insight and priority.`
- `Search interactions for Dr. Smith.`

## Verification

The frontend build and test suite were validated locally:

- `npm run build`
- `npm test -- --watchAll=false`

The backend `/chat` endpoint was also exercised directly to confirm log and search flows.