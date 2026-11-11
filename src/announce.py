"""Announced flyers: validation, URL normalization, keys and the run result (pure functions, no network)."""
from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import urlsplit, urlunsplit

SEEN_LIMIT = 200
ITEM_TYPE = "announced"
KEY_PREFIX = "announced|"


def normalize_url(url: str) -> str:
    """Lower-cases scheme and host, drops the fragment; raises ValueError unless an absolute http(s) URL."""
    text = (url or "").strip()
    parts = urlsplit(text)
    if parts.scheme.lower() not in ("http", "https") or not parts.netloc:
        raise ValueError("pdfUrl must be an absolute http(s) URL")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ""))


def item_key(normalized_url: str) -> str:
    return KEY_PREFIX + normalized_url


def _date(value: Any, name: str) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError(f"{name} must be an ISO date (YYYY-MM-DD)")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as e:
        raise ValueError(f"{name} must be an ISO date (YYYY-MM-DD)") from e


def validate(entries: Any) -> list[dict[str, Any]]:
    """Validates `announced` and returns normalized entries {url, title?, validFrom?, validTo?}.

    Duplicates (same normalized URL) collapse to the first. Raises ValueError naming the entry index.
    """
    if entries is None:
        return []
    if not isinstance(entries, list):
        raise ValueError("announced must be an array")
    out: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(entries):
        try:
            if not isinstance(entry, dict):
                raise ValueError("entry must be an object")
            url = normalize_url(entry.get("pdfUrl") or "")
            valid_from = _date(entry.get("validFrom"), "validFrom")
            valid_to = _date(entry.get("validTo"), "validTo")
            if valid_from and valid_to and valid_to < valid_from:
                raise ValueError("validTo must not be before validFrom")
            title = entry.get("title")
            if title is not None and not isinstance(title, str):
                raise ValueError("title must be a string")
        except ValueError as e:
            raise ValueError(f"announced[{index}]: {e}") from e
        if url in out:
            continue
        item: dict[str, Any] = {"url": url}
        if title:
            item["title"] = title
        if valid_from:
            item["validFrom"] = valid_from
        if valid_to:
            item["validTo"] = valid_to
        out[url] = item
    return list(out.values())


def build_run_result(entries: Any, state_in: dict | None) -> dict[str, Any]:
    announced = validate(entries)
    seen = list((state_in or {}).get("seen") or [])
    known = set(seen)
    new = [a for a in announced if item_key(a["url"]) not in known]
    items = []
    for a in new:
        meta: dict[str, Any] = {"type": ITEM_TYPE}
        for field in ("title", "validFrom", "validTo"):
            if field in a:
                meta[field] = a[field]
        items.append({"key": item_key(a["url"]), "url": a["url"], "meta": meta})
    seen_out = (seen + [item_key(a["url"]) for a in new])[-SEEN_LIMIT:]
    return {
        "items": items,
        "state": {"seen": seen_out},
        "metrics": {"announced": len(announced), "newAnnounced": len(new)},
        "checks": [],
    }
