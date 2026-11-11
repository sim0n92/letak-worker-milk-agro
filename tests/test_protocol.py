"""Proc-protocol v1.1 through stdin/stdout (subprocess, offline)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = next(p for p in (ROOT / "src" / "main.py", ROOT / "main.py") if p.is_file())


def _invoke(message: dict, tmp_path: Path):
    import os
    env = {**os.environ, "LOG_DIR": str(tmp_path)}
    p = subprocess.run([sys.executable, str(MAIN)], input=json.dumps(message) + "\n",
                       capture_output=True, text=True, env=env, timeout=30)
    lines = [json.loads(line) for line in p.stdout.splitlines() if line.strip()]
    return p.returncode, lines


def test_should_return_schemas_when_spec(tmp_path):
    code, lines = _invoke({"_action": "spec"}, tmp_path)
    data = [m for m in lines if m["type"] == "result"][0]["data"]
    assert code == 0 and data["protocol"] == "1.1" and "configSchema" in data and "outputSchema" in data


def test_should_report_count_when_check(tmp_path):
    code, lines = _invoke({"_action": "check", "announced": [{"pdfUrl": "https://h.sk/a.pdf"}]}, tmp_path)
    data = [m for m in lines if m["type"] == "result"][0]["data"]
    assert code == 0 and data == {"ok": True, "announced": 1}


def test_should_emit_one_result_with_items_when_run(tmp_path):
    code, lines = _invoke({"_action": "run", "announced": [{"pdfUrl": "https://h.sk/a.pdf"}], "state": None}, tmp_path)
    results = [m for m in lines if m["type"] == "result"]
    assert code == 0 and len(results) == 1
    assert results[0]["data"]["items"][0]["key"] == "announced|https://h.sk/a.pdf"


def test_should_exit_with_config_error_when_entry_invalid(tmp_path):
    code, lines = _invoke({"_action": "run", "announced": [{"pdfUrl": "nope"}]}, tmp_path)
    errors = [m for m in lines if m["type"] == "error"]
    assert code == 2 and errors and errors[0]["code"] == "config_error"


def test_should_print_manifest_version_when_version_flag(tmp_path):
    p = subprocess.run([sys.executable, str(MAIN), "--version"], capture_output=True, text=True,
                       env={**__import__("os").environ, "LOG_DIR": str(tmp_path)}, timeout=30)
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert p.stdout.strip() == manifest["version"]


def test_should_print_only_json_lines_when_run(tmp_path):
    _, lines = _invoke({"_action": "run"}, tmp_path)
    assert lines and all(m["type"] in ("progress", "result", "error") for m in lines)


def test_should_declare_the_mandatory_terminate_action_when_manifest_is_read():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert {"execute", "spec", "check", "run", "terminate"} <= set(manifest["actions"])
    assert "execute" in manifest["actions"]
