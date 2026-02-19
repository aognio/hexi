# ActionPlan Schema

Canonical JSON schema is stored at:

- `docs/contracts/action_plan.schema.json`

## Top-level

- `summary`: string
- `actions`: array of 1..20 action objects

## Action kinds

- `read`
- `write`
- `run`
- `emit`

## Emit action fields

- `event_type`
- `message`
- `blocking`
- optional `payload`

## Example

```json
{
  "summary": "add one test",
  "actions": [
    {"kind": "read", "path": "tests/test_parser.py"},
    {"kind": "write", "path": "tests/test_parser.py", "content": "..."},
    {"kind": "run", "command": "pytest tests/test_parser.py"}
  ]
}
```

## Ready-to-run examples

- `examples/action_plans/read_only.json`
- `examples/action_plans/write_file.json`
- `examples/action_plans/run_tests.json`
- `examples/action_plans/mixed_step.json`

```bash
hexi plan-check --file examples/action_plans/mixed_step.json
hexi apply --plan examples/action_plans/mixed_step.json --task "ActionPlan debug run"
```
