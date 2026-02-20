from __future__ import annotations

import json

from hexi.core.domain import Event, ModelConfig, Policy
from hexi.core.schemas import parse_action_plan
from hexi.core.service import RunStepService


class FakeMemory:
    def __init__(self) -> None:
        self.logged: list[Event] = []

    def ensure_initialized(self) -> None:
        return None

    def load_model_config(self) -> ModelConfig:
        return ModelConfig(provider="openai_compat", model="gpt-4o-mini", base_url="https://api.example.com/v1")

    def load_policy(self) -> Policy:
        return Policy(allow_commands=["python"], max_diff_chars=1000, max_file_read_chars=1000)

    def append_runlog(self, event: Event) -> None:
        self.logged.append(event)


class FakeEvents:
    def __init__(self) -> None:
        self.emitted: list[Event] = []

    def emit(self, event: Event) -> None:
        self.emitted.append(event)


class FakeWorkspace:
    def __init__(self) -> None:
        self.files = {"a.txt": "alpha"}

    def repo_root(self):  # pragma: no cover
        raise NotImplementedError

    def read_text(self, path: str, max_chars: int) -> str:
        return self.files[path][:max_chars]

    def write_text(self, path: str, content: str) -> None:
        self.files[path] = content

    def list_files(self, path: str | None, glob_pattern: str | None, limit: int) -> list[str]:
        return sorted(list(self.files.keys()))[:limit]

    def search_text(
        self,
        query: str,
        path: str | None,
        glob_pattern: str | None,
        limit: int,
        max_chars: int,
    ) -> list[dict[str, object]]:
        out: list[dict[str, object]] = []
        for name, content in self.files.items():
            for idx, line in enumerate(content.splitlines(), start=1):
                if query in line:
                    out.append({"path": name, "line": idx, "text": line[:max_chars]})
                    if len(out) >= limit:
                        return out
        return out

    def git_status(self) -> str:
        return " M a.txt"

    def git_diff(self, max_chars: int) -> str:
        return "diff --git a/a.txt b/a.txt\n+change"[:max_chars]


class FakeExec:
    def __init__(self, rc: int = 0) -> None:
        self.rc = rc
        self.commands: list[str] = []

    def run(self, command: str, policy: Policy):
        self.commands.append(command)
        return self.rc, "ok", ""


class StaticModel:
    def __init__(self, plan: str) -> None:
        self.plan = plan

    def plan_step(self, config: ModelConfig, system_prompt: str, user_prompt: str) -> str:
        return self.plan


def test_service_success_flow_with_all_action_types() -> None:
    plan = {
        "summary": "single step",
        "actions": [
            {"kind": "read", "path": "a.txt"},
            {"kind": "write", "path": "b.txt", "content": "beta"},
            {"kind": "run", "command": "python -V"},
            {
                "kind": "emit",
                "event_type": "progress",
                "message": "custom note",
                "blocking": False,
                "payload": {"k": "v"},
            },
        ],
    }
    memory = FakeMemory()
    events = FakeEvents()
    workspace = FakeWorkspace()
    executor = FakeExec(rc=0)
    model = StaticModel(json.dumps(plan))

    result = RunStepService(model, workspace, executor, events, memory).run_once("do work")

    assert result.success is True
    assert workspace.files["b.txt"] == "beta"
    assert executor.commands == ["python -V"]
    assert events.emitted[-2].type == "review"
    assert events.emitted[-1].type == "done"
    assert events.emitted[-1].payload["success"] is True
    assert len(memory.logged) == len(events.emitted)


def test_service_model_parse_failure_emits_error_and_done() -> None:
    memory = FakeMemory()
    events = FakeEvents()
    workspace = FakeWorkspace()
    executor = FakeExec(rc=0)
    model = StaticModel("not-json")

    result = RunStepService(model, workspace, executor, events, memory).run_once("do work")

    assert result.success is False
    types = [e.type for e in events.emitted]
    assert types == ["progress", "error", "done"]
    assert events.emitted[-1].blocking is True


def test_service_disallowed_command_fails_and_stops() -> None:
    plan = {
        "summary": "single step",
        "actions": [
            {"kind": "run", "command": "curl https://example.com"},
            {"kind": "write", "path": "should_not_write.txt", "content": "x"},
        ],
    }
    memory = FakeMemory()
    events = FakeEvents()
    workspace = FakeWorkspace()
    executor = FakeExec(rc=0)
    model = StaticModel(json.dumps(plan))

    result = RunStepService(model, workspace, executor, events, memory).run_once("do work")

    assert result.success is False
    assert "should_not_write.txt" not in workspace.files
    assert executor.commands == []
    assert events.emitted[-2].type == "review"
    assert events.emitted[-1].payload["success"] is False


def test_service_nonzero_command_exit_marks_run_unsuccessful() -> None:
    plan = {"summary": "single step", "actions": [{"kind": "run", "command": "python -V"}]}
    memory = FakeMemory()
    events = FakeEvents()
    workspace = FakeWorkspace()
    executor = FakeExec(rc=2)
    model = StaticModel(json.dumps(plan))

    result = RunStepService(model, workspace, executor, events, memory).run_once("do work")

    assert result.success is False
    run_event = next(e for e in events.emitted if e.one_line_summary.startswith("Ran command:"))
    assert run_event.blocking is True
    assert run_event.payload["exit_code"] == 2


def test_service_run_plan_executes_without_model() -> None:
    plan_json = {
        "summary": "manual apply",
        "actions": [
            {"kind": "write", "path": "manual.txt", "content": "ok"},
            {"kind": "emit", "event_type": "progress", "message": "applied", "blocking": False, "payload": {}},
        ],
    }
    memory = FakeMemory()
    events = FakeEvents()
    workspace = FakeWorkspace()
    executor = FakeExec(rc=0)
    parsed = parse_action_plan(json.dumps(plan_json))

    result = RunStepService(None, workspace, executor, events, memory).run_plan(
        task="apply task",
        plan=parsed,
        source="tests",
    )

    assert result.success is True
    assert workspace.files["manual.txt"] == "ok"
    assert events.emitted[-1].type == "done"


def test_service_executes_list_and_search_actions() -> None:
    plan = {
        "summary": "discover files",
        "actions": [
            {"kind": "list", "path": ".", "glob": "**/*.txt", "limit": 10},
            {"kind": "search", "query": "alpha", "path": ".", "glob": "**/*.txt", "limit": 10},
        ],
    }
    memory = FakeMemory()
    events = FakeEvents()
    workspace = FakeWorkspace()
    executor = FakeExec(rc=0)
    model = StaticModel(json.dumps(plan))

    result = RunStepService(model, workspace, executor, events, memory).run_once("do work")

    assert result.success is True
    summaries = [e.one_line_summary for e in events.emitted if e.type == "artifact"]
    assert any(s.startswith("Listed files") for s in summaries)
    assert any(s.startswith("Searched 'alpha'") for s in summaries)
