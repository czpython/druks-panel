# AGENTS.md

`druks-panel` is a standalone Druks app for durable decision review. Opportunity,
risk, and execution advisors assess a decision. A moderator combines the
assessments. Then the workflow parks for a human outcome.

## Read map

Use this read map:

- Read the Druks app contracts at https://docs.druks.ai/writing-an-app.
- Read the durable recovery semantics at https://docs.druks.ai/concepts#durability-and-recovery.
- Read `druks_panel/workflows.py` for orchestration and the human gate.
- Read `druks_panel/models.py` for decision persistence and its subject read-side.
- Read `druks_panel/dist/` for the standalone dashboard module in the wheel.

## Contracts

Apply these contracts:

- Install this distribution to register the app. Keep the
  `[project.entry-points."druks.apps"]` key and `Panel.name` set to `panel`.
- Keep decision policy, prompts, models, routes, and UI in the app. Keep durable
  execution, harnesses, gates, events, sandboxes, and the dashboard shell in Druks.
- Keep the app separate from Druks core. Do not make it a dependency of the Druks test suite.
- Describe recovery precisely. State that Druks reuses completed durable operations.
  State that work inside an interrupted operation can run again. Do not claim
  arbitrary-line resume or exactly-once side effects.
- Import only the documented Druks concern namespaces. Do not import Druks
  internals to make this example work.

## Verification

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
node --check druks_panel/dist/entry.js
```
