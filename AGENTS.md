# AGENTS.md

`druks-panel` is a standalone Druks app for durable decision review. A decision
is assessed by opportunity, risk, and execution advisors, synthesized by a
moderator, then parked for a human outcome.

## Read map

- Druks app contracts: https://docs.druks.ai/writing-an-app.
- Durable recovery semantics: https://docs.druks.ai/concepts#durability-and-recovery.
- `druks_panel/workflows.py` owns orchestration and the human gate.
- `druks_panel/models.py` owns decision persistence and its subject read-side.
- `druks_panel/dist/` is the standalone dashboard module shipped in the wheel.

## Contracts

- Installing this distribution is the registration. The
  `[project.entry-points."druks.apps"]` key and `Panel.name` are both `panel`.
- The app owns decision policy, prompts, models, routes, and UI. Druks owns
  durable execution, harnesses, gates, events, sandboxes, and the dashboard
  shell.
- The app demonstrates Druks but is not part of Druks core and must never become
  a dependency of the Druks test suite.
- Completed durable operations are reused during recovery. Work interrupted
  inside an operation may run again; do not claim arbitrary-line resume or
  exactly-once side effects.
- Import only the documented Druks concern namespaces. Do not reach into Druks
  internals to make this example work.

## Verify

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
node --check druks_panel/dist/entry.js
```
