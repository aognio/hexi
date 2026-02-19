from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hexi.cli import app
from hexi.core.schemas import parse_action_plan

runner = CliRunner()


def _init_git_repo(path: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("git is required for apply e2e tests")
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)


def test_apply_e2e_write_plan_creates_file_and_logs_done(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    init_result = runner.invoke(app, ["init"])
    assert init_result.exit_code == 0

    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "summary": "write a file",
                "actions": [
                    {"kind": "write", "path": "tmp/from_apply.txt", "content": "hello from apply\n"},
                    {
                        "kind": "emit",
                        "event_type": "progress",
                        "message": "write complete",
                        "blocking": False,
                        "payload": {"path": "tmp/from_apply.txt"},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    apply_result = runner.invoke(app, ["apply", "--plan", str(plan_path), "--task", "e2e apply"])
    assert apply_result.exit_code == 0
    assert (tmp_path / "tmp/from_apply.txt").read_text(encoding="utf-8") == "hello from apply\n"

    runlog = (tmp_path / ".hexi/runlog.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(runlog) >= 1
    last = json.loads(runlog[-1])
    assert last["type"] == "done"
    assert last["payload"]["success"] is True


def test_apply_e2e_disallowed_command_returns_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    init_result = runner.invoke(app, ["init"])
    assert init_result.exit_code == 0

    plan_path = tmp_path / "blocked.json"
    plan_path.write_text(
        json.dumps(
            {
                "summary": "attempt disallowed network command",
                "actions": [
                    {"kind": "run", "command": "curl https://example.com"},
                ],
            }
        ),
        encoding="utf-8",
    )

    apply_result = runner.invoke(app, ["apply", "--plan", str(plan_path)])
    assert apply_result.exit_code == 1

    runlog_lines = (tmp_path / ".hexi/runlog.jsonl").read_text(encoding="utf-8").splitlines()
    decoded = [json.loads(line) for line in runlog_lines]
    assert any(evt["type"] == "error" and "command not allowed" in evt["payload"].get("error", "") for evt in decoded)
    assert decoded[-1]["type"] == "done"
    assert decoded[-1]["payload"]["success"] is False


def test_example_action_plans_are_schema_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    plans_dir = root / "examples" / "action_plans"
    plan_files = sorted(plans_dir.glob("*.json"))
    assert len(plan_files) >= 4

    for plan_file in plan_files:
        raw = plan_file.read_text(encoding="utf-8")
        plan = parse_action_plan(raw)
        assert plan.summary
        assert len(plan.actions) >= 1
