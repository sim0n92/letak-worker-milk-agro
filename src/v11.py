"""Proc-protocol v1.1 adapter (spec / check / run) for the announced-flyers detect class."""
from __future__ import annotations

from typing import Any

import announce

PROTOCOL = "1.1"
ACTIONS = ("spec", "check", "run")
RETRY_AFTER_SEC = 300

CONFIG_ERROR = "config_error"
SYSTEM_ERROR = "system_error"

CONFIG_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "types": {"type": "array", "items": {"type": "string"}, "default": []},  # accepted for spec compatibility with the scrapers, ignored
        "announced": {"type": "array", "default": [], "items": {
            "type": "object", "required": ["pdfUrl"], "properties": {
                "pdfUrl": {"type": "string", "format": "uri"},
                "title": {"type": "string"},
                "validFrom": {"type": "string", "format": "date"},
                "validTo": {"type": "string", "format": "date"}}}},
        "state": {"type": ["object", "null"], "properties": {"seen": {"type": "array", "items": {"type": "string"}}}},
    },
    "additionalProperties": True,
}
OUTPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["items", "state", "metrics", "checks"],
    "properties": {
        "items": {"type": "array", "items": {"type": "object", "required": ["key", "url", "meta"], "properties": {
            "key": {"type": "string", "minLength": 1}, "url": {"type": "string", "minLength": 1},
            "meta": {"type": "object", "required": ["type"], "properties": {
                "type": {"type": "string"}, "title": {"type": "string"},
                "validFrom": {"type": "string"}, "validTo": {"type": "string"}}}}}},
        "state": {"type": "object", "required": ["seen"], "properties": {"seen": {"type": "array", "items": {"type": "string"}}}},
        "metrics": {"type": "object", "properties": {"announced": {"type": "integer"}, "newAnnounced": {"type": "integer"}}},
        "checks": {"type": "array"},
    },
}


def spec() -> dict[str, Any]:
    return {"configSchema": CONFIG_SCHEMA, "outputSchema": OUTPUT_SCHEMA, "protocol": PROTOCOL}


def classify(legacy_code: str | None) -> str:
    return CONFIG_ERROR if legacy_code == "INVALID_INPUT" else SYSTEM_ERROR


def error_data(code: str) -> dict[str, Any] | None:
    return None


def input_problem(input_data: dict[str, Any]) -> str | None:
    """Describes the first invalid field (announced / state), None when valid."""
    state = input_data.get("state")
    if state is not None:
        seen = state.get("seen") if isinstance(state, dict) else False
        if seen is False or (seen is not None and not (isinstance(seen, list) and all(isinstance(v, str) for v in seen))):
            return "state must be an object {seen: [string]}"
    try:
        announce.validate(input_data.get("announced"))
    except ValueError as e:
        return str(e)
    return None
