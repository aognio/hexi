from __future__ import annotations

from .domain import Event, StepResult, Thread
from .ports import EventSinkPort, ExecPort, MemoryPort, ModelPort, WorkspacePort
from .policy import command_allowed
from .schemas import ActionPlan, parse_action_plan

SYSTEM_PROMPT = """You are Hexi. Return only JSON matching this contract:
{
  \"summary\": string,
  \"actions\": [
    {\"kind\":\"read\",\"path\":\"...\"} |
    {\"kind\":\"write\",\"path\":\"...\",\"content\":\"...\"} |
    {\"kind\":\"run\",\"command\":\"...\"} |
    {\"kind\":\"emit\",\"event_type\":\"progress|question|review|artifact|error|done\",\"message\":\"...\",\"blocking\":false,\"payload\":{}}
  ]
}
Rules:
- One step only.
- Keep actions minimal.
- Use write with full file content.
- Never use network or destructive commands.
- Output JSON only, no markdown.
"""


class RunStepService:
    def __init__(
        self,
        model: ModelPort | None,
        workspace: WorkspacePort,
        executor: ExecPort,
        events: EventSinkPort,
        memory: MemoryPort,
    ) -> None:
        self.model = model
        self.workspace = workspace
        self.executor = executor
        self.events = events
        self.memory = memory

    def _emit(self, event: Event, acc: list[Event]) -> None:
        self.events.emit(event)
        self.memory.append_runlog(event)
        acc.append(event)

    def _run_plan_internal(self, task: str, thread_id: str, plan: ActionPlan, source: str) -> StepResult:
        policy = self.memory.load_policy()
        out_events: list[Event] = []

        initial = Event(
            type="progress",
            one_line_summary="Starting single-step run",
            blocking=False,
            payload={"task": task, "thread_id": thread_id, "source": source},
        )
        self._emit(initial, out_events)
        self._emit(
            Event(
                type="progress",
                one_line_summary=f"Action plan ready: {plan.summary}",
                blocking=False,
                payload={"actions": len(plan.actions)},
            ),
            out_events,
        )

        success = True
        for action in plan.actions:
            try:
                if action.kind == "read":
                    assert action.path is not None
                    content = self.workspace.read_text(action.path, policy.max_file_read_chars)
                    self._emit(
                        Event(
                            type="artifact",
                            one_line_summary=f"Read {action.path}",
                            blocking=False,
                            payload={"path": action.path, "content": content},
                        ),
                        out_events,
                    )
                elif action.kind == "write":
                    assert action.path is not None
                    assert action.content is not None
                    self.workspace.write_text(action.path, action.content)
                    self._emit(
                        Event(
                            type="artifact",
                            one_line_summary=f"Wrote {action.path}",
                            blocking=False,
                            payload={"path": action.path, "bytes": len(action.content.encode("utf-8"))},
                        ),
                        out_events,
                    )
                elif action.kind == "run":
                    assert action.command is not None
                    if not command_allowed(action.command, policy):
                        raise PermissionError(f"command not allowed: {action.command}")
                    code, stdout, stderr = self.executor.run(action.command, policy)
                    self._emit(
                        Event(
                            type="artifact",
                            one_line_summary=f"Ran command: {action.command}",
                            blocking=code != 0,
                            payload={"command": action.command, "exit_code": code, "stdout": stdout, "stderr": stderr},
                        ),
                        out_events,
                    )
                    if code != 0:
                        success = False
                else:
                    self._emit(
                        Event(
                            type=action.event_type or "progress",
                            one_line_summary=action.message or "model message",
                            blocking=bool(action.blocking),
                            payload=action.payload or {},
                        ),
                        out_events,
                    )
            except Exception as exc:
                success = False
                self._emit(
                    Event(
                        type="error",
                        one_line_summary=f"Action failed: {action.kind}",
                        blocking=True,
                        payload={"error": str(exc)},
                    ),
                    out_events,
                )
                break

        final_status = self.workspace.git_status()
        final_diff = self.workspace.git_diff(policy.max_diff_chars)
        self._emit(
            Event(
                type="review",
                one_line_summary="Step review",
                blocking=False,
                payload={
                    "git_status": final_status,
                    "git_diff": final_diff,
                    "suggestion": "Run tests next" if success else "Need user decision",
                },
            ),
            out_events,
        )
        self._emit(
            Event(type="done", one_line_summary="Run completed", blocking=not success, payload={"success": success}),
            out_events,
        )
        return StepResult(success=success, events=out_events)

    def run_plan(self, task: str, plan: ActionPlan, source: str = "manual") -> StepResult:
        self.memory.ensure_initialized()
        thread = Thread(id="single-step", task=task)
        return self._run_plan_internal(task=task, thread_id=thread.id, plan=plan, source=source)

    def run_once(self, task: str) -> StepResult:
        self.memory.ensure_initialized()
        model_config = self.memory.load_model_config()
        thread = Thread(id="single-step", task=task)
        policy = self.memory.load_policy()
        status = self.workspace.git_status()
        diff = self.workspace.git_diff(policy.max_diff_chars)
        user_prompt = (
            f"Task:\n{task}\n\n"
            f"Repo status:\n{status}\n\n"
            f"Current diff (truncated):\n{diff}\n"
        )

        try:
            if self.model is None:
                raise RuntimeError("model adapter is required for run_once")
            raw_plan = self.model.plan_step(model_config, SYSTEM_PROMPT, user_prompt)
            plan = parse_action_plan(raw_plan)
        except Exception as exc:
            out_events: list[Event] = []
            initial = Event(
                type="progress",
                one_line_summary="Starting single-step run",
                blocking=False,
                payload={"task": task, "thread_id": thread.id, "source": "model"},
            )
            self._emit(initial, out_events)
            ev = Event(
                type="error",
                one_line_summary="Model output parsing failed",
                blocking=True,
                payload={"error": str(exc)},
            )
            self._emit(ev, out_events)
            done = Event(type="done", one_line_summary="Run failed", blocking=True, payload={"success": False})
            self._emit(done, out_events)
            return StepResult(success=False, events=out_events)
        return self._run_plan_internal(task=task, thread_id=thread.id, plan=plan, source="model")
