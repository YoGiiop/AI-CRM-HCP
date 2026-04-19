from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agents.langgraph_agent import run_agent
from app.core.config import FRONTEND_ORIGIN
from app.db import Base, engine, SessionLocal
from app.models.interaction import Interaction

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI CRM HCP API",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    interaction: Dict = Field(default_factory=dict)


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest):
    response = run_agent(req.message, req.interaction)
    interaction = response.get("interaction")
    tool = response.get("tool")

    if tool == "log_interaction" and interaction and interaction.get("hcp_name"):
        saved_record = _create_interaction(interaction)
        response["interaction"] = {**interaction, "id": saved_record.id}

    if tool == "edit_interaction" and interaction and interaction.get("id"):
        saved_record = _update_interaction(interaction)
        if saved_record is not None:
            response["interaction"] = {**interaction, "id": saved_record.id}

    return response


def _create_interaction(interaction: Dict):
    db = SessionLocal()
    try:
        new_entry = Interaction(**_db_payload(interaction))
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        return new_entry
    finally:
        db.close()


def _update_interaction(interaction: Dict):
    db = SessionLocal()
    try:
        existing = db.query(Interaction).filter(Interaction.id == interaction["id"]).first()

        if existing is None:
            return None

        for field, value in _db_payload(interaction).items():
            setattr(existing, field, value)

        db.commit()
        db.refresh(existing)
        return existing
    finally:
        db.close()


def _db_payload(interaction: Dict):
    materials = interaction.get("materials_shared") or []
    return {
        "hcp_name": interaction.get("hcp_name"),
        "date": interaction.get("date"),
        "time": interaction.get("time"),
        "interaction_type": interaction.get("interaction_type"),
        "topics": interaction.get("topics"),
        "sentiment": interaction.get("sentiment"),
        "materials_shared": ", ".join(materials),
        "summary": interaction.get("summary") or interaction.get("outcomes"),
        "follow_up": interaction.get("follow_up"),
        "insight": interaction.get("insight"),
        "priority": interaction.get("priority"),
    }
