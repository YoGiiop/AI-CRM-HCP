import json
import re
from datetime import datetime, timedelta

from dateutil import parser
from groq import Groq

from app.core.config import (
    GROQ_API_KEY,
    GROQ_FALLBACK_MODEL,
    GROQ_PRIMARY_MODEL,
    GROQ_ROUTING_MODEL,
)

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def _get_client():
    if client is None:
        raise RuntimeError("GROQ_API_KEY is not configured")
    return client


def ask_llm_raw(prompt: str, system_prompt: str = "You route CRM assistant actions."):
    try:
        response = _create_completion(
            [GROQ_ROUTING_MODEL, GROQ_FALLBACK_MODEL],
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        return str(exc)


def ask_llm_structured(
    prompt: str,
    schema_description: str,
    *,
    normalize_dates: bool = False,
):
    try:
        response = _create_completion(
            [GROQ_PRIMARY_MODEL, GROQ_FALLBACK_MODEL, GROQ_ROUTING_MODEL],
            [
                {
                    "role": "system",
                    "content": (
                        "You are an AI-first CRM copilot for healthcare field reps. "
                        "Return only valid JSON that matches the requested schema. "
                        "Do not wrap the JSON in markdown. Omit commentary."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Schema:\n{schema_description}\n\n"
                        f"Task:\n{prompt}"
                    ),
                },
            ],
        )

        raw_output = response.choices[0].message.content or "{}"
        cleaned = raw_output.strip().replace("```json", "").replace("```", "")
        parsed = json.loads(cleaned)

        if normalize_dates and isinstance(parsed, dict):
            parsed = normalize_datetime(parsed, prompt, fill_missing_datetime=True)

        return parsed
    except Exception as exc:
        return {"error": str(exc)}


def _create_completion(models: list[str], messages: list[dict]):
    last_error = None

    for model in dict.fromkeys(models):
        try:
            return _get_client().chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
            )
        except Exception as exc:
            last_error = exc

            if "model_decommissioned" not in str(exc) and "not found" not in str(exc).lower():
                raise

    raise last_error if last_error else RuntimeError("No Groq model could be used")


def normalize_datetime(
    data: dict,
    user_input: str = "",
    *,
    fill_missing_datetime: bool,
):
    now = datetime.now()
    text = user_input.lower().strip()
    current_date = _resolve_date(text, data.get("date"), now)
    current_time = _resolve_time(text, data.get("time"), now)

    should_set_date = fill_missing_datetime or bool(data.get("date")) or _has_relative_date(text)
    should_set_time = fill_missing_datetime or bool(data.get("time")) or _has_time_value(text)

    if should_set_date and current_date:
        data["date"] = current_date.strftime("%Y-%m-%d")

    if should_set_time and current_time:
        data["time"] = current_time.strftime("%H:%M")

    return data


def _has_relative_date(text: str):
    return any(word in text for word in ["today", "tomorrow", "yesterday", "tmrw", "yday"])


def _has_time_value(text: str):
    return bool(
        re.search(r"\b\d{1,2}:\d{2}\s?(am|pm)?\b", text)
        or re.search(r"\b\d{1,2}\s?(am|pm)\b", text)
    )


def _resolve_date(text: str, llm_value: str, now: datetime):
    if any(word in text for word in ["yesterday", "yday"]):
        return now - timedelta(days=1)
    if any(word in text for word in ["tomorrow", "tmrw"]):
        return now + timedelta(days=1)
    if "today" in text:
        return now
    if llm_value:
        try:
            return parser.parse(llm_value, fuzzy=True)
        except (ValueError, TypeError, OverflowError):
            return now
    return now


def _resolve_time(text: str, llm_value: str, now: datetime):
    time_patterns = [
        r"\b\d{1,2}:\d{2}\s?(am|pm)?\b",
        r"\b\d{1,2}\s?(am|pm)\b",
    ]

    for pattern in time_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return parser.parse(match.group(0))
            except (ValueError, TypeError, OverflowError):
                break

    if llm_value:
        try:
            return parser.parse(llm_value)
        except (ValueError, TypeError, OverflowError):
            return now

    return now