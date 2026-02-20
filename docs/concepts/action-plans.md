# Action Plans

Hexi requires model output in a strict JSON action-plan format.

## Core shape

```json
{
  "summary": "one sentence",
  "actions": [
    {"kind": "read", "path": "..."},
    {"kind": "list", "path": "src", "glob": "**/*.py", "limit": 100},
    {"kind": "search", "query": "RunStepService", "path": "src", "glob": "**/*.py", "limit": 20},
    {"kind": "write", "path": "...", "content": "..."},
    {"kind": "run", "command": "..."},
    {"kind": "emit", "event_type": "progress", "message": "...", "blocking": false, "payload": {}}
  ]
}
```

## Why strict JSON

- predictable parser behavior,
- testable validation paths,
- clear adapter boundaries.

## Validation outcomes

- Invalid shape -> parse error event + done failure.
- Valid shape + disallowed action -> execution error event + review + done failure.

## Practical advice

When tuning prompts or models, optimize for:

- fewer actions,
- deterministic writes,
- explicit run commands that align with policy allowlists.
