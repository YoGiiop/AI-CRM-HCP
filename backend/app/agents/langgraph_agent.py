import json
import re
from typing import TypedDict

from langgraph.graph import StateGraph

from app.agents.llm import ask_llm_raw
from app.agents.tools import (
    edit_interaction_tool,
    insight_tool,
    log_interaction_tool,
    search_interaction_tool,
    suggest_followup_tool,
    summarize_interaction_tool,
)


class AgentState(TypedDict):
    message: str
    interaction: dict
    response: dict


def detect_intent(message: str):
    normalized_message = message.strip().lower()

    if re.match(r"^(?:can\s+you\s+|could\s+you\s+|please\s+)?(?:search|find|lookup|look up|show|list)\b", normalized_message):
        return "search"

    if re.search(r"\b(suggest|follow[ -]?up|next step(?:s)?|next best action(?:s)?|next action(?:s)?|what should i do next|what next)\b", normalized_message):
        return "followup"

    if re.search(r"\b(summarize|summari[sz]e|summary|recap)\b", normalized_message):
        return "summary"

    if re.search(r"\b(analy[sz]e|analysis|insight|priority)\b", normalized_message):
        return "insight"

    if re.search(r"\b(edit|update|change|correct|fix|revise)\b", normalized_message):
        return "edit_interaction"

    prompt = f"""
    Classify the CRM assistant intent for this user message:
    {message}

    Allowed intents:
    - log_interaction
    - edit_interaction
    - followup
    - summary
    - insight
    - search

    Return JSON only in this format:
    {{ "intent": "log_interaction" }}
    """

    raw = ask_llm_raw(prompt)

    try:
        cleaned = raw.strip().replace("```json", "").replace("```", "")
        parsed = json.loads(cleaned)
        return parsed.get("intent", "log_interaction")
    except (TypeError, ValueError, json.JSONDecodeError):
        return "log_interaction"


def router(state: AgentState):
    intent = detect_intent(state["message"])
    mapping = {
        "log_interaction": "log",
        "edit_interaction": "edit",
        "followup": "followup",
        "summary": "summary",
        "insight": "insight",
        "search": "search",
    }
    return mapping.get(intent, "log")


def log_node(state: AgentState):
    interaction = log_interaction_tool(state["message"])
    return {
        "interaction": interaction,
        "response": {
            "tool": "log_interaction",
            "assistant_message": "Interaction captured from chat and pushed into the form.",
            "interaction": interaction,
        },
    }


def edit_node(state: AgentState):
    interaction = edit_interaction_tool(state["message"], state["interaction"])
    return {
        "interaction": interaction,
        "response": {
            "tool": "edit_interaction",
            "assistant_message": "Requested corrections were applied to the existing interaction.",
            "interaction": interaction,
        },
    }


def followup_node(state: AgentState):
    guard_response = _require_logged_interaction(
        state,
        tool="suggest_followup",
        assistant_message="Log an interaction first, then ask for next-best actions.",
    )
    if guard_response is not None:
        return guard_response

    interaction = {**state["interaction"], **suggest_followup_tool(state["interaction"])}
    return {
        "interaction": interaction,
        "response": {
            "tool": "suggest_followup",
            "assistant_message": "Next-best actions were generated for the field rep.",
            "interaction": interaction,
        },
    }


def summary_node(state: AgentState):
    guard_response = _require_logged_interaction(
        state,
        tool="summarize_interaction",
        assistant_message="Log an interaction first, then ask for a CRM summary.",
    )
    if guard_response is not None:
        return guard_response

    interaction = {**state["interaction"], **summarize_interaction_tool(state["interaction"])}
    return {
        "interaction": interaction,
        "response": {
            "tool": "summarize_interaction",
            "assistant_message": "Outcomes and CRM summary were generated from the current interaction.",
            "interaction": interaction,
        },
    }


def insight_node(state: AgentState):
    guard_response = _require_logged_interaction(
        state,
        tool="generate_insight",
        assistant_message="Log an interaction first, then ask for insight or priority.",
    )
    if guard_response is not None:
        return guard_response

    interaction = {**state["interaction"], **insight_tool(state["interaction"])}
    return {
        "interaction": interaction,
        "response": {
            "tool": "generate_insight",
            "assistant_message": "Commercial insight and priority were inferred from the interaction.",
            "interaction": interaction,
        },
    }


def search_node(state: AgentState):
    result = search_interaction_tool(state["message"])
    results = result.get("results", [])
    return {
        "response": {
            "tool": "search_interactions",
            "assistant_message": (
                f"Found {len(results)} matching interaction(s)."
                if results
                else "No matching interactions found for that search."
            ),
            "results": results,
        }
    }


builder = StateGraph(AgentState)

builder.add_node("log", log_node)
builder.add_node("edit", edit_node)
builder.add_node("followup", followup_node)
builder.add_node("summary", summary_node)
builder.add_node("insight", insight_node)
builder.add_node("search", search_node)

builder.set_conditional_entry_point(router)

graph = builder.compile()


def _require_logged_interaction(state: AgentState, *, tool: str, assistant_message: str):
    if _has_logged_interaction(state.get("interaction") or {}):
        return None

    return {
        "response": {
            "tool": tool,
            "assistant_message": assistant_message,
        }
    }


def _has_logged_interaction(interaction: dict):
    if not isinstance(interaction, dict):
        return False

    meaningful_fields = (
        "id",
        "hcp_name",
        "interaction_type",
        "date",
        "time",
        "attendees",
        "topics",
        "sentiment",
        "outcomes",
        "follow_up",
        "summary",
        "insight",
        "priority",
    )

    if any(interaction.get(field) for field in meaningful_fields):
        return True

    if interaction.get("materials_shared") or interaction.get("samples_distributed"):
        return True

    return False


def run_agent(message: str, current_data: dict | None = None):
    result = graph.invoke(
        {
            "message": message,
            "interaction": current_data or {},
            "response": {},
        }
    )
    return result["response"]