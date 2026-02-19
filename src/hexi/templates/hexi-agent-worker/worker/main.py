import sys
from pathlib import Path

from hexi.adapters.events_console import ConsoleEventSink
from hexi.adapters.exec_local import LocalExec
from hexi.adapters.memory_file import FileMemory
from hexi.adapters.model_openai_compat import OpenAICompatModel
from hexi.adapters.workspace_local_git import LocalGitWorkspace
from hexi.core.service import RunStepService


def main() -> int:
    task = " ".join(sys.argv[1:]).strip() or "Add one small test"
    ws = LocalGitWorkspace(Path.cwd())
    mem = FileMemory(ws.repo_root())
    mem.ensure_initialized()
    mem.apply_api_key_to_env("openai_compat")

    svc = RunStepService(
        model=OpenAICompatModel(),
        workspace=ws,
        executor=LocalExec(),
        events=ConsoleEventSink(),
        memory=mem,
    )
    result = svc.run_once(task)
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
