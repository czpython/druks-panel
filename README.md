# Druks Panel

Druks Panel turns a consequential question into an inspectable decision process.
Three independent advisors examine opportunity, risk, and execution. A moderator
synthesizes their arguments, then the workflow parks until a human chooses to
proceed, revise, or pass.

It is deliberately small: one subject, one workflow, four agents, one human
gate. That makes it an approachable example of a real
[Druks](https://github.com/czpython/druks) app without turning the framework into
the app.

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

- a separately packaged app registered through `druks.apps`
- strict structured outputs for every agent
- durable, replayable orchestration across agent calls and persistence steps
- a subject-backed gate that can remain parked across restarts
- app-owned models, migrations, HTTP routes, prompts, and dashboard UI

Druks reuses completed durable operations when a workflow recovers. An operation
interrupted before completion may run again, so this app does not claim
exactly-once external effects.

## Install for development

Clone Druks and this repository beside each other, then install Panel into the
Druks environment:

```bash
git clone https://github.com/czpython/druks.git
git clone https://github.com/czpython/druks-panel.git
cd druks
uv sync --dev
uv pip install -e ../druks-panel
```

Start the Druks development stack using the
[development guide](https://docs.druks.ai/development). Panel appears in the app
switcher after Druks restarts and discovers the installed entry point.

For an image-based deployment, extend the Druks image and install the package
into its existing virtual environment:

```dockerfile
FROM ghcr.io/czpython/druks:latest
RUN uv pip install "git+https://github.com/czpython/druks-panel.git"
```

Use that image for the Druks `web` service, run `druks init-db`, and restart the
service. Connect at least one Claude harness before starting a panel.

## Use

Open **Panel** in the Druks dashboard, enter the decision and its context, then
start deliberation. The page updates as the advisors and moderator finish. When
the run parks, read the synthesis and record the human outcome.

Agent defaults are ordinary Druks agent settings. An operator can change the
model, effort, and timeout for each advisor from the dashboard without changing
this package.

## Develop

Tests use the Druks pytest plugin and its isolated Postgres test database:

```bash
uv sync --dev
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
node --check druks_panel/dist/entry.js
```

The database defaults match Druks: Postgres at `localhost:5432`, user and
password `druks`, database `druks_test`. Override it with
`DRUKS_TEST_DATABASE_URL`.
