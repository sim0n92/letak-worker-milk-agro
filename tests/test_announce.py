"""Announced flyers: pure functions, offline."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import announce  # noqa: E402


def test_should_build_item_with_key_and_meta_when_entry_valid():
    result = announce.build_run_result([{"pdfUrl": "https://Host.sk/a/b.pdf", "title": "T", "validFrom": "2026-11-01"}], None)
    assert result["items"] == [{"key": "announced|https://host.sk/a/b.pdf", "url": "https://host.sk/a/b.pdf",
                                "meta": {"type": "announced", "title": "T", "validFrom": "2026-11-01"}}]
    assert "validTo" not in result["items"][0]["meta"]
    assert result["metrics"] == {"announced": 1, "newAnnounced": 1}


def test_should_collapse_to_one_item_when_url_differs_by_host_case_or_fragment():
    result = announce.build_run_result([{"pdfUrl": "https://HOST.sk/a.pdf#x"}, {"pdfUrl": "https://host.sk/a.pdf"}], None)
    assert len(result["items"]) == 1


def test_should_emit_nothing_when_url_already_seen():
    key = "announced|https://host.sk/a.pdf"
    result = announce.build_run_result([{"pdfUrl": "https://host.sk/a.pdf"}], {"seen": [key]})
    assert result["items"] == []
    assert result["state"]["seen"] == [key]
    assert result["metrics"] == {"announced": 1, "newAnnounced": 0}


@pytest.mark.parametrize("entry", [
    {"pdfUrl": "https://h.sk/a.pdf", "validFrom": "2026-11-10", "validTo": "2026-11-01"},
    {"pdfUrl": "ftp://h.sk/a.pdf"},
    {"pdfUrl": "a.pdf"},
    {"pdfUrl": ""},
    {},
    {"pdfUrl": "https://h.sk/a.pdf", "validFrom": "10.11.2026"},
])
def test_should_raise_value_error_when_entry_invalid(entry):
    with pytest.raises(ValueError, match=r"announced\[0\]"):
        announce.validate([entry])


@pytest.mark.parametrize("value", [None, []])
def test_should_return_no_items_when_announced_empty_or_absent(value):
    result = announce.build_run_result(value, None)
    assert result["items"] == [] and result["state"] == {"seen": []}


def test_should_cap_state_at_200_when_many_announced():
    entries = [{"pdfUrl": f"https://h.sk/{i}.pdf"} for i in range(250)]
    result = announce.build_run_result(entries, None)
    assert len(result["items"]) == 250
    assert len(result["state"]["seen"]) == 200
    assert result["state"]["seen"][-1] == "announced|https://h.sk/249.pdf"
