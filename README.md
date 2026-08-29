# Druks Panel

Druks Panel turns an important question into an inspectable decision process.
Three independent advisors examine opportunity, risk, and execution. A
moderator combines their arguments. Then the workflow parks until a human
selects proceed, revise, or pass.

The app has one subject, one workflow, four agents, and one human gate. This
small scope makes it a clear example of a
[Druks](https://github.com/czpython/druks) app. Druks Panel remains separate
from the framework.

## What it demonstrates

```text
decision
   ├─ opportunity advisor
   ├─ risk advisor
   └─ execution advisor
            ↓
        moderator
            ↓
   durable human decision
```

The app provides these parts:

- A separate app package that uses `druks.apps`
- Strict structured outputs for each agent
- Durable orchestration across agent calls and persistence steps
- A subject-backed gate that can remain parked across restarts
- App-owned models, migrations, HTTP routes, prompts, and dashboard UI.

Druks reuses completed durable operations when a workflow recovers. An operation
that stops before completion can run again. Thus, this app does not claim
exactly-once external effects.

## Install for development

Clone Druks and this repository into adjacent directories. Then install Panel
in the Druks environment:

```bash
git clone https://github.com/czpython/druks.git
git clone https://github.com/czpython/druks-panel.git
cd druks
uv sync --dev
uv pip install -e ../druks-panel
```

Use the [development guide](https://docs.druks.ai/development) to start the
Druks development stack. Restart Druks after the installation. Druks finds the
entry point and shows Panel in the app switcher.

For an image deployment, extend the Druks image. Install the package in its
existing virtual environment:

```dockerfile
FROM ghcr.io/czpython/druks:latest
RUN uv pip install "git+https://github.com/czpython/druks-panel.git"
```

Use that image for the Druks `web` service. Run `druks init-db`. Restart the
service. Connect at least one Claude harness before you start a panel.

## Use

Open **Panel** in the Druks dashboard. Enter the decision and its context. Then
start the deliberation. The page updates after each advisor and the moderator
finish. When the run parks, read the synthesis. Record the human outcome.

Agent defaults use standard Druks agent settings. An operator can change the
model, effort, and timeout for each advisor in the dashboard. This change does
not require a package change.

## Develop

The tests use the Druks pytest plugin and an isolated Postgres test database:

```bash
uv sync --dev
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
node --check druks_panel/dist/entry.js
```

The database defaults match Druks. Postgres uses `localhost:5432`. The user and
password are `druks`. The database is `druks_test`. Set
`DRUKS_TEST_DATABASE_URL` to use a different database.
