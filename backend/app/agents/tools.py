import re

from sqlalchemy import or_

from app.agents.llm import ask_llm_structured, normalize_datetime
from app.db import SessionLocal
from app.models.interaction import Interaction

INTERACTION_SCHEMA = """
{
  "hcp_name": "",
  "interaction_type": "",
  "date": "",
  "time": "",
  "attendees": "",
  "topics": "",
  "materials_shared": [],
  "samples_distributed": [],
  "sentiment": "",
  "outcomes": "",
  "follow_up": "",
  "ai_suggested_follow_up": [],
  "summary": "",
  "insight": "",
  "priority": ""
}
""".strip()

INTERACTION_FIELDS = {
    "id",
    "hcp_name",
    "interaction_type",
    "date",
    "time",
    "attendees",
    "topics",
    "materials_shared",
    "samples_distributed",
    "sentiment",
    "outcomes",
    "follow_up",
    "ai_suggested_follow_up",
    "summary",
    "insight",
    "priority",
}

FOLLOW_UP_FIELDS = {"follow_up", "ai_suggested_follow_up"}
SUMMARY_FIELDS = {"outcomes", "summary"}
INSIGHT_FIELDS = {"insight", "priority"}

FOLLOW_UP_SCHEMA = """
{
  "follow_up": "",
  "ai_suggested_follow_up": []
}
""".strip()

SUMMARY_SCHEMA = """
{
  "outcomes": "",
  "summary": ""
}
""".strip()

INSIGHT_SCHEMA = """
{
  "insight": "",
  "priority": ""
}
""".strip()


def log_interaction_tool(user_input: str):
    prompt = (
        "Extract the HCP interaction details from the rep's chat message. "
        "Infer a reasonable interaction type, sentiment, and outcomes when possible. "
        "Use arrays for materials_shared, samples_distributed, and ai_suggested_follow_up.\n\n"
        f"Message:\n{user_input}"
    )
    result = ask_llm_structured(prompt, INTERACTION_SCHEMA, normalize_dates=True)
    normalized = _normalize_interaction(result)
    return _post_process_logged_interaction(normalized, user_input)


def edit_interaction_tool(user_input: str, existing_data: dict):
    prompt = (
        "You are updating an existing logged CRM interaction. "
        "Return only the fields that the user explicitly changed. "
        "Do not rewrite unchanged values. Use arrays for list fields.\n\n"
        f"Existing interaction:\n{existing_data}\n\n"
        f"User correction:\n{user_input}"
    )
    updates = ask_llm_structured(prompt, INTERACTION_SCHEMA)

    if isinstance(updates, dict):
        updates = normalize_datetime(updates, user_input, fill_missing_datetime=False)
        merged = {
            **existing_data,
            **_normalize_interaction(updates, partial=True, allowed_fields=INTERACTION_FIELDS),
        }
        return _normalize_interaction(merged)

    return _normalize_interaction(existing_data)


def suggest_followup_tool(data: dict):
    prompt = (
        "Generate the next best actions for the field rep based on this HCP interaction. "
        "Provide one short follow-up summary plus up to three bullet-ready next actions.\n\n"
        f"Interaction:\n{data}"
    )
    return _normalize_interaction(
        ask_llm_structured(prompt, FOLLOW_UP_SCHEMA),
        partial=True,
        allowed_fields=FOLLOW_UP_FIELDS,
    )


def summarize_interaction_tool(data: dict):
    prompt = (
        "Summarize the interaction for CRM documentation. "
        "Return concise outcomes and a short executive summary.\n\n"
        f"Interaction:\n{data}"
    )
    return _normalize_interaction(
        ask_llm_structured(prompt, SUMMARY_SCHEMA),
        partial=True,
        allowed_fields=SUMMARY_FIELDS,
    )


def insight_tool(data: dict):
    prompt = (
        "Analyze the HCP interaction and return one concise insight plus a priority value of low, medium, or high.\n\n"
        f"Interaction:\n{data}"
    )
    return _normalize_interaction(
        ask_llm_structured(prompt, INSIGHT_SCHEMA),
        partial=True,
        allowed_fields=INSIGHT_FIELDS,
    )


def search_interaction_tool(query: str):
    search_text = _normalize_search_query(query)

    db = SessionLocal()

    try:
        results = db.query(Interaction).filter(
            or_(
                Interaction.hcp_name.ilike(f"%{search_text}%"),
                Interaction.topics.ilike(f"%{search_text}%"),
                Interaction.summary.ilike(f"%{search_text}%"),
            )
        ).all()

        return {
            "results": [
                {
                    "id": record.id,
                    "hcp_name": record.hcp_name,
                    "date": record.date,
                    "time": record.time,
                    "topics": record.topics,
                    "summary": record.summary,
                }
                for record in results
            ]
        }
    finally:
        db.close()


def _normalize_search_query(query: str):
    normalized = query.strip()

    patterns = [
        r"^(can\s+you|could\s+you|would\s+you|please)\b",
        r"^(search|find|lookup|look up|show|list)\b",
        r"\bme\b",
        r"\byou\b",
        r"\b(all|any|the)\b",
        r"\b(interactions?|records?|entries|history)\b",
        r"\b(with|for|about|on|regarding|related to|matching)\b",
    ]

    for pattern in patterns:
        normalized = re.sub(pattern, " ", normalized, flags=re.IGNORECASE)
        normalized = normalized.strip()

    normalized = re.sub(r"\s+", " ", normalized).strip(" ,.-")
    return normalized or query.strip()


def _normalize_interaction(data: dict, partial: bool = False, allowed_fields: set[str] | None = None):
    if not isinstance(data, dict):
        return {} if partial else _interaction_defaults()

    normalized = {} if partial else _interaction_defaults()

    for key, value in data.items():
        if allowed_fields is not None and key not in allowed_fields:
            continue
        if key in {"materials_shared", "samples_distributed", "ai_suggested_follow_up"}:
            normalized[key] = _to_list(value)
        elif value is None:
            normalized[key] = ""
        else:
            normalized[key] = value

    if not partial:
        normalized["materials_shared"] = _to_list(normalized.get("materials_shared"))
        normalized["samples_distributed"] = _to_list(normalized.get("samples_distributed"))
        normalized["ai_suggested_follow_up"] = _to_list(normalized.get("ai_suggested_follow_up"))

    return normalized


def _post_process_logged_interaction(data: dict, user_input: str):
    processed = {**data}

    doctor_names = _extract_hcp_names(user_input)
    if doctor_names:
        processed["hcp_name"] = doctor_names[0]
        if len(doctor_names) > 1 and not processed.get("attendees"):
            processed["attendees"] = ", ".join(doctor_names)

    normalized_sentiment = _infer_sentiment(user_input, processed.get("sentiment", ""))
    if normalized_sentiment:
        processed["sentiment"] = normalized_sentiment

    return processed


def _extract_hcp_names(text: str):
    matches = re.findall(r"\bDr\.?\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?", text)
    unique_matches = []
    for match in matches:
        clean_match = re.sub(r"\s+", " ", match.replace("Dr.", "Dr")).strip()
        if clean_match not in unique_matches:
            unique_matches.append(clean_match)
    return unique_matches


def _infer_sentiment(user_input: str, current_sentiment: str):
    text = user_input.lower()
    matches = list(re.finditer(r"\b(positive|negative|neutral)\b", text))
    if matches:
        return matches[-1].group(1)

    normalized_current = (current_sentiment or "").strip().lower()
    if normalized_current in {"positive", "negative", "neutral"}:
        return normalized_current

    if normalized_current == "mixed":
        return "neutral"

    return normalized_current


def _interaction_defaults():
    return {
        "id": None,
        "hcp_name": "",
        "interaction_type": "",
        "date": "",
        "time": "",
        "attendees": "",
        "topics": "",
        "materials_shared": [],
        "samples_distributed": [],
        "sentiment": "",
        "outcomes": "",
        "follow_up": "",
        "ai_suggested_follow_up": [],
        "summary": "",
        "insight": "",
        "priority": "",
    }


def _to_list(value):
    if isinstance(value, list):
        normalized_items = []
        for item in value:
            normalized_item = _normalize_list_item(item)
            if normalized_item:
                normalized_items.append(normalized_item)
        return normalized_items
    if isinstance(value, str):
        return [item.strip() for item in re.split(r",|\n", value) if item.strip()]
    return []


def _normalize_list_item(item):
    if isinstance(item, dict):
        for key in ("action", "label", "title", "name"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    item_text = str(item).strip()
    return item_text