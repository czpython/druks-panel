# AGENTS.md

`druks-panel` is a standalone Druks app for durable decision review. Opportunity,
risk, and execution advisors assess a decision. A moderator combines the
assessments. Then the workflow parks for a human outcome.

## Read map

- Read the Druks app contracts at https://docs.druks.ai/writing-an-app.
- Read the page, block, value, field, and action catalog at
  https://docs.druks.ai/druks-ui.
- Read the durable recovery semantics at https://docs.druks.ai/concepts#durability-and-recovery.
- Read `druks_panel/workflows.py` for orchestration and the human gate.
- Read `druks_panel/models.py` for decision persistence and its subject read-side.
- Read `druks_panel/pages.py` for the screens the dashboard renders.

## Contracts

- Install this distribution to register the app. Keep the
  `[project.entry-points."druks.apps"]` key and `Panel.name` set to `panel`.
- Keep decision policy, prompts, models, routes, and pages in the app. Keep durable
  execution, harnesses, gates, events, sandboxes, and the dashboard shell in Druks.
- Keep the app separate from Druks core. Do not make it a dependency of the Druks test suite.
- Screens are Python. `pages.py` declares them and the dashboard renders them.
  This app writes no JavaScript and ships no `dist/`.
- A page function is a pure read. Druks calls it again on load, on an event, on a
  reconnect, and on a retry. It must not write, start work, publish an event, or
  answer a gate. Every write goes through a route that an `Action` names by its
  `operation_id`.
- `Panel.navigation` names declared pages. Each name must be a static top-level page.
- Describe recovery precisely. State that Druks reuses completed durable operations.
  State that work inside an interrupted operation can run again. Do not claim
  arbitrary-line resume or exactly-once side effects.
- Import only the documented Druks concern namespaces: `druks.apps`,
  `druks.agents`, `druks.workflows`, `druks.db`, `druks.schemas`, `druks.ui`,
  and `druks.signals`. Do not import Druks internals to make this example work.
- This repository has no tests. Do not add a test suite or a test dependency.

## Verification

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
```
