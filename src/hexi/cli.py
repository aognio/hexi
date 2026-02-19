from __future__ import annotations

import json
import random
import shutil
import subprocess
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from typer.main import get_command

from hexi import __version__
from hexi.adapters.events_console import ConsoleEventSink
from hexi.adapters.exec_local import LocalExec
from hexi.adapters.memory_file import FileMemory
from hexi.adapters.model_anthropic_compat import AnthropicCompatModel
from hexi.adapters.model_openai_compat import OpenAICompatModel
from hexi.adapters.model_openrouter_http import OpenRouterHTTPModel
from hexi.adapters.model_openrouter_sdk import OpenRouterSDKModel
from hexi.adapters.workspace_local_git import LocalGitWorkspace
from hexi.core.schemas import ActionPlanError, parse_action_plan
from hexi.core.service import RunStepService

app = typer.Typer(
    help="Hexi CLI (v0.2.0): single-step coding-agent runtime.",
    no_args_is_help=True,
)
console = Console()

SUPPORTED_PROVIDERS = ["openrouter_http", "openrouter_sdk", "openai_compat", "anthropic_compat"]
TEMPLATES = [
    "hexi-python-lib",
    "hexi-fastapi-service",
    "hexi-typer-cli",
    "hexi-data-job",
    "hexi-agent-worker",
]
DEMO_RANDOM_PROMPTS: dict[str, list[str]] = {
    "hexi-python-lib": [
        "create an agentic codemod helper that proposes safe refactors and add tests",
        "add an autonomous flaky-test triage helper and test it",
    ],
    "hexi-fastapi-service": [
        "add endpoint to receive coding tasks and queue single-step agent actions with tests",
        "add endpoint that summarizes git diff review for agentic runs and test it",
    ],
    "hexi-typer-cli": [
        "add 'agent-plan' subcommand to draft coding action plans and tests",
        "add 'agent-review' subcommand to summarize code diffs and tests",
    ],
    "hexi-data-job": [
        "add job that analyzes runlogs and reports recurring agent failures with tests",
        "add pipeline stage that scores agent action quality and tests",
    ],
    "hexi-agent-worker": [
        "add retry guardrails for failed agent steps and tests",
        "add structured post-step reviewer for code edits and tests",
    ],
}


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"hexi {__version__}")
        raise typer.Exit()


@app.callback()
def app_callback(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show Hexi version and exit.",
        is_eager=True,
        callback=_version_callback,
    ),
) -> None:
    """Hexi command group callback."""


def _workspace_and_memory() -> tuple[LocalGitWorkspace, FileMemory]:
    ws = LocalGitWorkspace(Path.cwd())
    memory = FileMemory(ws.repo_root())
    return ws, memory


def _bootstrap_memory() -> tuple[FileMemory, Path, bool]:
    try:
        ws = LocalGitWorkspace(Path.cwd())
        root = ws.repo_root()
        return FileMemory(root), root, True
    except RuntimeError:
        root = Path.cwd()
        return FileMemory(root), root, False


def _pick_model(provider: str):
    if provider == "openai_compat":
        return OpenAICompatModel()
    if provider == "anthropic_compat":
        return AnthropicCompatModel()
    if provider == "openrouter_http":
        return OpenRouterHTTPModel()
    if provider == "openrouter_sdk":
        return OpenRouterSDKModel()
    raise typer.BadParameter(f"unsupported provider: {provider}")


def _error_and_exit(message: str, code: int = 2) -> None:
    console.print(Panel(Text(f"Error: {message}", style="bold red"), border_style="red", title="Hexi"))
    raise typer.Exit(code=code)


def _copy_template_tree(src: Path, destination: Path, force: bool) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()) and not force:
        raise RuntimeError(f"destination is not empty: {destination}. Use --force to overwrite-compatible copy")

    for item in src.iterdir():
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=force)
        else:
            if target.exists() and not force:
                raise RuntimeError(f"file exists: {target}. Re-run with --force")
            shutil.copy2(item, target)


def _local_template_roots() -> list[Path]:
    return [
        Path(__file__).resolve().parents[2] / "templates",
        Path.cwd() / "templates",
    ]


def _copy_template(template: str, destination: Path, force: bool) -> None:
    for root in _local_template_roots():
        src = root / template
        if src.exists():
            _copy_template_tree(src, destination, force)
            return

    package_templates = files("hexi").joinpath("templates").joinpath(template)
    if package_templates.is_dir():
        with as_file(package_templates) as src:
            _copy_template_tree(Path(src), destination, force)
            return

    raise FileNotFoundError(f"template not found: {template}")


def _validate_destination(destination: Path, force: bool) -> None:
    if not destination.exists():
        return
    if destination.is_file():
        raise RuntimeError(f"destination is a file: {destination}. Choose a directory path.")
    if destination.is_dir() and any(destination.iterdir()) and not force:
        raise RuntimeError(f"destination is not empty: {destination}. Use --force to overwrite-compatible copy.")


def _generate_demo_ideas(cfg_provider: str, cfg_model: str, cfg_base_url: str | None, cfg_api_style: str | None) -> list[dict[str, str]]:
    model_cfg = type("TmpModelCfg", (), {})()
    model_cfg.provider = cfg_provider
    model_cfg.model = cfg_model
    model_cfg.base_url = cfg_base_url
    model_cfg.api_style = cfg_api_style
    model = _pick_model(cfg_provider)
    nonce = random.randint(100000, 999999)
    raw = model.plan_step(
        model_cfg,
        (
            "You are Hexi Demo Ideator.\n"
            "Hexi is a Pythonic library/CLI for creating agentic coders: systems that read code, propose constrained action plans, "
            "edit files safely, run allowlisted commands, and emit structured events.\n"
            "Hexi projects are about code generation and code-change automation workflows, not generic apps.\n"
            "Output must be strict JSON only; no markdown, no prose outside JSON."
        ),
        (
            f"Run nonce: {nonce}.\n"
            "Generate exactly 3 distinct, practical project ideas as JSON with this shape only:\n"
            "{\"ideas\":[{\"title\":str,\"template\":str,\"prompt\":str}]}\n\n"
            f"Template must be one of: {TEMPLATES}.\n"
            "Each idea must be explicitly about agentic coding capabilities, such as:\n"
            "- automated code edits with safety constraints\n"
            "- test generation/repair loops\n"
            "- migration assistants for codebases\n"
            "- code review augmentation using structured events\n"
            "- runlog analysis and coding workflow diagnostics\n\n"
            "Hard constraints:\n"
            "- no generic websites\n"
            "- no general consumer apps\n"
            "- no ideas unrelated to software engineering automation\n"
            "- prompts must request code changes/tests/docs in a repository\n\n"
            "Quality bar:\n"
            "- concrete and buildable in a tiny starter project\n"
            "- clear engineering value for developers\n"
            "- each of the 3 ideas must be meaningfully different\n"
        ),
    )
    data: dict[str, Any]
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise RuntimeError("ideas response must be a JSON object")
        data = parsed
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or start >= end:
            snippet = raw[:200].replace("\n", " ")
            raise RuntimeError(f"ideas response was not valid JSON. Raw starts with: {snippet}")
        parsed = json.loads(raw[start : end + 1])
        if not isinstance(parsed, dict):
            raise RuntimeError("ideas response must be a JSON object")
        data = parsed
    ideas = data.get("ideas", [])
    if not isinstance(ideas, list) or len(ideas) != 3:
        raise RuntimeError("invalid ideas response")
    out: list[dict[str, str]] = []
    for item in ideas:
        if not isinstance(item, dict):
            raise RuntimeError("invalid idea item")
        title = str(item.get("title", "")).strip()
        template = str(item.get("template", "")).strip()
        prompt = str(item.get("prompt", "")).strip()
        if not title or template not in TEMPLATES or not prompt:
            raise RuntimeError("invalid idea fields")
        out.append({"title": title, "template": template, "prompt": prompt})
    random.shuffle(out)
    return out


def _ideas_mode_available(cfg_provider: str, cfg_model: str, cfg_base_url: str | None, cfg_api_style: str | None, key_source: str | None) -> tuple[bool, str]:
    if key_source is None:
        return False, "missing API key"
    if cfg_provider not in SUPPORTED_PROVIDERS:
        return False, f"unsupported provider '{cfg_provider}'"
    try:
        model_cfg = type("TmpModelCfg", (), {})()
        model_cfg.provider = cfg_provider
        model_cfg.model = cfg_model
        model_cfg.base_url = cfg_base_url
        model_cfg.api_style = cfg_api_style
        model = _pick_model(cfg_provider)
        _ = model.plan_step(
            model_cfg,
            "You are a connectivity probe. Reply with one word: ok.",
            "Say ok.",
        )
        return True, "ready"
    except Exception as exc:
        return False, str(exc)


@app.command("help", help="Show command help.")
def help_cmd() -> None:
    """Display help text explicitly as `hexi help`."""
    command = get_command(app)
    ctx = typer.Context(command)
    console.print(command.get_help(ctx))


@app.command("version", help="Print Hexi version.")
def version_cmd() -> None:
    """Print semantic version."""
    console.print(f"hexi {__version__}")


@app.command("plan-check", help="Validate and troubleshoot an ActionPlan JSON payload.")
def plan_check_cmd(
    file: Path | None = typer.Option(None, "--file", help="Path to ActionPlan JSON file."),
    json_input: str | None = typer.Option(None, "--json", help="Inline ActionPlan JSON string."),
) -> None:
    """Validate ActionPlan JSON and show parsed action summary."""
    if file is None and json_input is None:
        _error_and_exit("Provide one input via --file or --json")
    if file is not None and json_input is not None:
        _error_and_exit("Use only one input source: --file or --json")

    raw = ""
    source = ""
    if file is not None:
        if not file.exists():
            _error_and_exit(f"ActionPlan file not found: {file}")
        raw = file.read_text(encoding="utf-8")
        source = str(file)
    else:
        assert json_input is not None
        raw = json_input
        source = "inline --json"

    try:
        plan = parse_action_plan(raw)
    except ActionPlanError as exc:
        console.print(
            Panel(
                f"Invalid ActionPlan from [bold]{source}[/bold]\n\n{exc}",
                title="Plan Check Failed",
                border_style="red",
            )
        )
        console.print(
            "Hints:\n"
            "- ensure top-level keys are exactly: summary, actions\n"
            "- ensure each action has required fields by kind\n"
            "- ensure JSON is strict (no trailing commas/comments)"
        )
        raise typer.Exit(code=1)

    info = Table(show_header=False)
    info.add_row("Source", source)
    info.add_row("Summary", plan.summary)
    info.add_row("Action count", str(len(plan.actions)))
    console.print(Panel(info, title="Plan Check Passed", border_style="green"))

    actions_table = Table(title="Actions", show_header=True, header_style="bold cyan")
    actions_table.add_column("#", justify="right")
    actions_table.add_column("Kind")
    actions_table.add_column("Target/Command")
    actions_table.add_column("Notes")
    for idx, action in enumerate(plan.actions, start=1):
        target = action.path or action.command or "-"
        notes = "-"
        if action.kind == "write":
            notes = f"bytes={len((action.content or '').encode('utf-8'))}"
        elif action.kind == "emit":
            notes = f"event={action.event_type}, blocking={action.blocking}"
        actions_table.add_row(str(idx), action.kind, target, notes)
    console.print(actions_table)


@app.command("apply", help="Execute a validated ActionPlan JSON file directly (debug/replay mode).")
def apply_cmd(
    plan: Path = typer.Option(..., "--plan", help="Path to ActionPlan JSON file."),
    task: str = typer.Option("Apply prebuilt action plan", "--task", help="Task label used in run events."),
) -> None:
    """Execute one ActionPlan file without calling the model."""
    if not plan.exists():
        _error_and_exit(f"ActionPlan file not found: {plan}")
    raw = plan.read_text(encoding="utf-8")
    try:
        parsed = parse_action_plan(raw)
    except ActionPlanError as exc:
        console.print(
            Panel(
                f"Invalid ActionPlan from [bold]{plan}[/bold]\n\n{exc}",
                title="Apply Failed",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    try:
        ws, memory = _workspace_and_memory()
    except RuntimeError as exc:
        _error_and_exit(str(exc))

    memory.ensure_initialized()
    info = Table(show_header=False)
    info.add_row("Plan file", str(plan))
    info.add_row("Summary", parsed.summary)
    info.add_row("Actions", str(len(parsed.actions)))
    info.add_row("Task label", task)
    console.print(Panel(info, title="Hexi Apply", border_style="blue"))

    service = RunStepService(
        model=None,
        workspace=ws,
        executor=LocalExec(),
        events=ConsoleEventSink(),
        memory=memory,
    )
    result = service.run_plan(task=task, plan=parsed, source=str(plan))
    raise typer.Exit(code=0 if result.success else 1)


@app.command("init", help="Initialize .hexi config/runlog files in this folder (or git root when available).")
def init_cmd() -> None:
    """Create Hexi state files in bootstrap or repo mode."""
    memory, root, is_git_repo = _bootstrap_memory()
    memory.ensure_initialized()
    if not is_git_repo:
        console.print(
            Panel(
                "No git repository detected. Initialized in current directory.\n"
                "If you run `git init` later, rerun `hexi init` from your intended repo root.",
                border_style="yellow",
                title="Bootstrap Mode",
            )
        )
    console.print(
        Panel(
            f"Initialized Hexi in [bold]{root / '.hexi'}[/bold]",
            title="Setup Complete",
            border_style="green",
        )
    )


@app.command("onboard", help="Interactive setup for provider/model and optional local API key storage.")
def onboard_cmd() -> None:
    """Configure provider, model, and optional local key in .hexi/local.toml."""
    memory, root, is_git_repo = _bootstrap_memory()
    memory.ensure_initialized()

    if not is_git_repo:
        console.print(
            Panel(
                "No git repository detected. Onboarding will write into current directory.",
                border_style="yellow",
                title="Bootstrap Mode",
            )
        )
    console.print(Panel(f"Onboarding in repo: [bold]{root}[/bold]", border_style="cyan", title="Hexi Onboard"))
    providers = Table(show_header=True, header_style="bold cyan")
    providers.add_column("Provider")
    providers.add_column("Notes")
    providers.add_row("openai_compat", "OpenAI-compatible chat/completions")
    providers.add_row("anthropic_compat", "Anthropic-compatible messages")
    providers.add_row("openrouter_http", "OpenRouter via raw HTTP")
    providers.add_row("openrouter_sdk", "OpenRouter via SDK")
    console.print(providers)

    provider = typer.prompt("Provider", default="openai_compat").strip()
    if provider not in SUPPORTED_PROVIDERS:
        _error_and_exit(f"unsupported provider '{provider}'")

    default_model = "gpt-4o-mini"
    if provider in {"openrouter_http", "openrouter_sdk"}:
        default_model = "openai/gpt-4o-mini"
    elif provider == "anthropic_compat":
        default_model = "claude-3-5-sonnet-latest"
    model = typer.prompt("Model", default=default_model).strip()

    api_style: str | None = None
    if provider == "openrouter_http":
        api_style = typer.prompt("OpenRouter API style (openai|anthropic)", default="openai").strip().lower()
        if api_style not in {"openai", "anthropic"}:
            _error_and_exit("api style must be openai or anthropic")

    save_key = typer.confirm("Paste and store API key in .hexi/local.toml now?", default=True)
    api_key: str | None = None
    if save_key:
        api_key = typer.prompt("API key", hide_input=True).strip()
        if not api_key:
            console.print("[yellow]Warning: empty key provided; skipping key storage[/yellow]")
            api_key = None

    memory.write_local_onboarding(provider=provider, model=model, api_style=api_style, api_key=api_key)
    key_source = memory.apply_api_key_to_env(provider)

    summary = Table(show_header=False)
    summary.add_row("Provider", provider)
    summary.add_row("Model", model)
    if api_style:
        summary.add_row("API style", api_style)
    summary.add_row("Local config", str(memory.local_config_path))
    summary.add_row("API key source", key_source or "none")
    console.print(Panel(summary, title="Onboarding Result", border_style="green"))


@app.command("new", help="Scaffold a project from a built-in Hexi template (non-interactive by default).")
def new_cmd(
    template: str = typer.Option("hexi-python-lib", "--template", help="Template name."),
    name: str | None = typer.Option(None, "--name", help="Project directory name."),
    path: Path = typer.Option(Path("."), "--path", help="Parent path for project output."),
    git_init: bool = typer.Option(False, "--git-init", help="Initialize git repository after scaffold."),
    force: bool = typer.Option(False, "--force", help="Allow overwrite-compatible copy into non-empty destination."),
    interactive: bool = typer.Option(False, "--interactive", help="Prompt for template/name before scaffolding."),
) -> None:
    """Create a new project from packaged templates."""
    chosen_template = template
    chosen_name = name
    if interactive:
        chosen_template = typer.prompt("Template", default=template).strip()
        chosen_name = typer.prompt("Project name (blank for current path)", default=name or "").strip() or None
    if chosen_template not in TEMPLATES:
        _error_and_exit(f"unknown template '{chosen_template}'. Available: {', '.join(TEMPLATES)}")

    destination = path / chosen_name if chosen_name else path
    _validate_destination(destination, force)
    _copy_template(chosen_template, destination, force)

    if git_init:
        subprocess.run(["git", "init"], cwd=destination, check=False, capture_output=True)

    info = Table(show_header=False)
    info.add_row("Template", chosen_template)
    info.add_row("Destination", str(destination.resolve()))
    info.add_row("Git initialized", "yes" if git_init else "no")
    console.print(Panel(info, title="Hexi New", border_style="green"))
    console.print("Next: `cd <project> && hexi doctor && make test`")


@app.command("demo", help="Fancy interactive demo: generate or pick project ideas, then scaffold a template.")
def demo_cmd(
    path: Path = typer.Option(Path("."), "--path", help="Parent path for demo output."),
    name: str | None = typer.Option(None, "--name", help="Project directory name."),
    git_init: bool = typer.Option(True, "--git-init/--no-git-init", help="Initialize git after scaffold."),
    force: bool = typer.Option(False, "--force", help="Allow overwrite-compatible copy into non-empty destination."),
) -> None:
    """Run model-driven project idea flow and scaffold selected template."""
    project_name = name or typer.prompt("Project name", default="hexi-demo-project").strip()
    destination = path / project_name
    try:
        _validate_destination(destination, force)
    except RuntimeError as exc:
        _error_and_exit(str(exc))

    memory, _, _ = _bootstrap_memory()
    memory.ensure_initialized()
    cfg = memory.load_model_config()
    memory.apply_api_key_to_env(cfg.provider)
    _, key_source = memory.resolve_api_key(cfg.provider)
    ideas_ok, ideas_reason = _ideas_mode_available(cfg.provider, cfg.model, cfg.base_url, cfg.api_style, key_source)

    disclaimer = Text(
        "QUALITY DISCLAIMER: generated demo ideas depend on your configured language model. "
        "Model capability and reliability directly affect output quality.",
        style="blink bold black on bright_yellow",
    )
    console.print(Panel(disclaimer, title="⚠ DEMO MODE NOTICE ⚠", border_style="bright_yellow"))
    console.print(
        Panel(
            "Note: Hexi demo code-generating features are still being implemented.",
            title="Demo Note",
            border_style="cyan",
        )
    )

    mode_table = Table(title="Hexi Demo Mode", show_header=True, header_style="bold cyan")
    mode_table.add_column("Option")
    mode_table.add_column("Description")
    mode_table.add_row("random", "Pick a random template + random starter prompt")
    if ideas_ok:
        mode_table.add_row("ideas", "Ask configured model for 3 ideas")
    mode_table.add_row("custom", "Choose template manually and type your own prompt")
    console.print(mode_table)
    if not ideas_ok:
        console.print(
            Panel(
                f"Ideas mode is unavailable: {ideas_reason}",
                title="Demo Notice",
                border_style="yellow",
            )
        )
        if typer.confirm("Show connectivity debug hint now?", default=False):
            console.print("Run: `hexi doctor --probe-model` to inspect provider/key/model connectivity.")
    default_mode = "ideas" if ideas_ok else "random"
    mode = typer.prompt("Mode", default=default_mode).strip().lower()
    allowed_modes = {"random", "custom"} | ({"ideas"} if ideas_ok else set())
    if mode not in allowed_modes:
        _error_and_exit(f"mode must be one of: {', '.join(sorted(allowed_modes))}")

    selected_template = "hexi-python-lib"
    selected_prompt = "add one useful improvement with tests"

    if mode == "random":
        selected_template = random.choice(TEMPLATES)
        selected_prompt = random.choice(DEMO_RANDOM_PROMPTS[selected_template])
    elif mode == "custom":
        selected_template = typer.prompt("Template", default="hexi-python-lib").strip()
        if selected_template not in TEMPLATES:
            _error_and_exit(f"unknown template '{selected_template}'")
        selected_prompt = typer.prompt("Starter prompt", default=selected_prompt).strip()
    else:
        ideas: list[dict[str, str]]
        try:
            ideas = _generate_demo_ideas(cfg.provider, cfg.model, cfg.base_url, cfg.api_style)
        except Exception as exc:
            console.print(Panel(f"Idea generation failed ({exc}); using random fallback.", border_style="yellow", title="Demo"))
            selected_template = random.choice(TEMPLATES)
            selected_prompt = random.choice(DEMO_RANDOM_PROMPTS[selected_template])
            ideas = []

        if ideas:
            ideas_table = Table(title="Pick an idea", show_header=True, header_style="bold magenta")
            ideas_table.add_column("#")
            ideas_table.add_column("Title")
            ideas_table.add_column("Template")
            ideas_table.add_column("Prompt")
            for idx, idea in enumerate(ideas, start=1):
                ideas_table.add_row(str(idx), idea["title"], idea["template"], idea["prompt"])
            console.print(ideas_table)

            choice = typer.prompt("Choose 1/2/3 or type custom", default="1").strip()
            if choice in {"1", "2", "3"}:
                picked = ideas[int(choice) - 1]
                selected_template = picked["template"]
                selected_prompt = picked["prompt"]
            else:
                selected_template = typer.prompt("Template", default="hexi-python-lib").strip()
                if selected_template not in TEMPLATES:
                    _error_and_exit(f"unknown template '{selected_template}'")
                selected_prompt = choice

    _copy_template(selected_template, destination, force)

    if git_init:
        subprocess.run(["git", "init"], cwd=destination, check=False, capture_output=True)

    summary = Table(show_header=False)
    summary.add_row("Template", selected_template)
    summary.add_row("Prompt", selected_prompt)
    summary.add_row("Destination", str(destination.resolve()))
    summary.add_row("Git initialized", "yes" if git_init else "no")
    console.print(Panel(summary, title="Hexi Demo Result", border_style="green"))

    run_customization = typer.confirm("Run one Hexi customization step now?", default=True)
    if run_customization:
        if not git_init:
            console.print(
                Panel(
                    "Customization step skipped because git is not initialized.\n"
                    "Re-run with --git-init (default) or run `git init` in the project first.",
                    title="Demo Customization",
                    border_style="yellow",
                )
            )
        else:
            proc = subprocess.run(
                ["hexi", "run", selected_prompt],
                cwd=destination,
                check=False,
                capture_output=True,
                text=True,
            )
            if proc.returncode == 0:
                console.print(
                    Panel(
                        "Customization step completed successfully.\n"
                        "Your scaffold should now reflect the selected demo idea.",
                        title="Demo Customization",
                        border_style="green",
                    )
                )
            else:
                details = (proc.stderr or proc.stdout or "").strip()
                snippet = details[:600] if details else "No output captured."
                console.print(
                    Panel(
                        f"Customization step failed (exit={proc.returncode}).\n{snippet}",
                        title="Demo Customization",
                        border_style="yellow",
                    )
                )

    console.print(
        "Try next:\n"
        f"  cd {destination}\n"
        "  hexi doctor\n"
        f"  hexi run \"{selected_prompt}\""
    )


@app.command("run", help="Execute one Hexi agent step for a task and emit structured events.")
def run_cmd(task: str) -> None:
    """Run one model-planned step and exit."""
    try:
        ws, memory = _workspace_and_memory()
    except RuntimeError as exc:
        _error_and_exit(str(exc))
    memory.ensure_initialized()
    config = memory.load_model_config()
    memory.apply_api_key_to_env(config.provider)
    model = _pick_model(config.provider)

    console.print(
        Panel(
            f"Task: [bold]{task}[/bold]\nProvider: [bold]{config.provider}[/bold]\nModel: [bold]{config.model}[/bold]",
            title="Hexi Run",
            border_style="blue",
        )
    )

    service = RunStepService(
        model=model,
        workspace=ws,
        executor=LocalExec(),
        events=ConsoleEventSink(),
        memory=memory,
    )
    result = service.run_once(task)
    raise typer.Exit(code=0 if result.success else 1)


@app.command("diff", help="Print git diff for the current repository.")
def diff_cmd() -> None:
    """Show working tree diff."""
    try:
        ws, _ = _workspace_and_memory()
    except RuntimeError as exc:
        _error_and_exit(str(exc))
    diff = ws.git_diff(max_chars=20000)
    console.print(Panel(diff or "(no changes)", title="Git Diff", border_style="magenta"))


@app.command("doctor", help="Run environment, config, and credential diagnostics (optionally with live model probe).")
def doctor_cmd(
    probe_model: bool = typer.Option(
        False,
        "--probe-model/--no-probe-model",
        help="Call the configured model and run the 'What model are you?' probe.",
    ),
) -> None:
    """Run verbose diagnostics for Hexi setup and provider readiness."""
    memory, root, is_git_repo = _bootstrap_memory()
    memory.ensure_initialized()
    cfg = memory.load_model_config()
    memory.apply_api_key_to_env(cfg.provider)
    _, key_source = memory.resolve_api_key(cfg.provider)

    issues: list[str] = []
    if key_source is None:
        issues.append(f"Missing API key for provider '{cfg.provider}'")

    checks = Table(title="Doctor checks", show_header=True, header_style="bold cyan")
    checks.add_column("Check")
    checks.add_column("Status")
    checks.add_column("Details")
    checks.add_row(
        "Workspace",
        "[green]PASS[/green]" if is_git_repo else "[yellow]WARN[/yellow]",
        "Git repository detected" if is_git_repo else "No git repository yet (bootstrap mode)",
    )
    checks.add_row("Config", "[green]PASS[/green]", ".hexi files are present")
    checks.add_row("Provider", "[green]PASS[/green]" if cfg.provider in SUPPORTED_PROVIDERS else "[red]FAIL[/red]", cfg.provider)
    checks.add_row("API key", "[green]PASS[/green]" if key_source else "[yellow]WARN[/yellow]", key_source or "none")

    probe_details = "not requested"
    probe_status = "[cyan]SKIP[/cyan]"
    if probe_model:
        if key_source is None:
            probe_status = "[yellow]WARN[/yellow]"
            probe_details = "skipped: missing API key"
        elif cfg.provider not in SUPPORTED_PROVIDERS:
            probe_status = "[red]FAIL[/red]"
            probe_details = "unsupported provider"
        else:
            try:
                model = _pick_model(cfg.provider)
                probe_raw = model.plan_step(
                    cfg,
                    "You are a diagnostic assistant. Reply with one short plain sentence only.",
                    "What model are you? equation: model_identity = provider/model_name",
                )
                probe_status = "[green]PASS[/green]"
                probe_details = (probe_raw or "").strip().replace("\n", " ")[:180] or "(empty response)"
            except Exception as exc:
                probe_status = "[yellow]WARN[/yellow]"
                probe_details = f"probe failed: {exc}"

    checks.add_row("Model probe", probe_status, probe_details)

    repo_display = str(root)
    if is_git_repo:
        try:
            ws = LocalGitWorkspace(root)
            repo_display = str(ws.repo_root())
        except RuntimeError:
            pass

    border = "green" if not issues else "yellow"
    title = "Doctor report"
    info = Table(show_header=False)
    info.add_row("Repo root", repo_display)
    info.add_row("Provider", cfg.provider)
    info.add_row("Model", cfg.model)
    info.add_row("Base URL", cfg.base_url or "(default)")
    info.add_row("API style", cfg.api_style or "(n/a)")
    info.add_row("Config", str(memory.config_path))
    info.add_row("Local config", str(memory.local_config_path))
    info.add_row("Runlog", str(memory.runlog_path))
    info.add_row("API key source", key_source or "none")
    console.print(Panel(info, title=title, border_style=border))
    console.print(checks)
    console.print(f"API key source: {key_source or 'none'}")
    if not probe_model:
        console.print("Tip: run `hexi doctor --probe-model` for live model identity check.")

    if issues:
        for issue in issues:
            console.print(f"[yellow][WARN][/yellow] {issue}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
