# Sporty Group Test Task

Portfolio project combining a sportsbook-style Angular application with a separate AI coding-agent workflow tool.

The main app is a single-page Angular experience for browsing sports leagues from TheSportsDB API. Alongside it, the repository includes an agentic developer workflow UI and FastAPI backend that can inspect the codebase, propose changes, wait for human approval, apply approved changes, and run verification.

## What This Showcases

- Angular 22 standalone application architecture
- A separate Angular tool app in the same workspace
- Typed HttpClient services with RxJS caching
- Angular Signals for workflow/UI state
- Component-driven SCSS UI design
- FastAPI backend design
- Agent tool orchestration with OpenAI-compatible APIs through OpenRouter
- Human-in-the-loop change approval
- Git/diff/test/build workflow concepts
- Persistent workflow state and backend guardrails
- Focused unit tests and lint/type-check validation

## Applications

### Sportsbook App

The sportsbook app lives under `src/app` and remains the product-facing application.

Features:

- Lists sports leagues from TheSportsDB
- Searches leagues by name
- Filters by sport
- Loads available season badges per league
- Uses a dark sportsbook-inspired visual style

Run it with:

```bash
npm start
```

Default URL:

```text
http://localhost:4200
```

### AI Workflow Tool

The workflow tool lives under `src/workflow` and runs as a separate Angular application. It is designed as a developer tool for maintaining the sportsbook app, not as part of the public sportsbook UI.

It visualizes an AI coding-agent workflow similar to a lightweight mix of a pull request review, CI pipeline, and agent execution viewer.

Features:

- Submit a coding task
- View agent analysis
- Inspect recorded tool activity
- Review proposed file diffs
- Approve or reject proposed changes
- Apply approved changes through the backend only
- Run verification after apply
- Request a repair proposal after verification failure
- Preserve human approval before every code-changing step

Run it with:

```bash
npm run start:workflow
```

Default URL:

```text
http://localhost:4300
```

## Backend Agent

The backend lives under `backend` and uses FastAPI.

The agent follows a controlled workflow:

1. Creates a workflow for the requested task.
2. Inspects project files through bounded tools.
3. Searches and reads relevant code.
4. Can inspect Git state and diffs.
5. Can run verification checks.
6. Produces a stored proposal containing file diffs.
7. Waits for explicit human approval.
8. Applies the backend-owned proposal.
9. Runs verification.
10. Allows a repair cycle when verification fails.

The frontend never sends proposed source code back during approval. It sends only `workflow_id` and `proposal_id`; the backend owns the stored proposal.

### Backend Endpoints

- `POST /analyze`
- `POST /apply-change`
- `POST /reject-change`
- `POST /repair/{workflow_id}`
- `GET /workflow/{workflow_id}`

### Persistence And Guardrails

Workflows are persisted to:

```text
backend/.data/workflows.json
```

That runtime state is intentionally ignored by Git.

Operational limits and guardrails include:

- maximum problem length
- maximum stored workflows
- maximum proposals per workflow
- maximum proposal files
- maximum proposal size
- bounded file reads
- bounded search results
- bounded Git diff output
- operation locking to prevent duplicate apply/repair requests
- stale proposal protection using file hashes
- frontend-only edit restrictions for agent proposals
- repair attempt limits

## AI Provider

The backend uses OpenRouter through the OpenAI-compatible Python client.

Expected environment variables in `backend/.env`:

```env
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-4o
OPENROUTER_MAX_TOKENS=4000
```

`OPENROUTER_MODEL` and `OPENROUTER_MAX_TOKENS` are configurable. The backend sets the OpenRouter base URL to:

```text
https://openrouter.ai/api/v1
```

## Project Structure

```text
src/
  app/
    components/        # Sportsbook UI components
    features/          # Sportsbook feature pages
    models/            # Sportsbook API models
    services/          # Sportsbook API services
  workflow/
    components/        # Workflow presentation components
    models/            # Workflow domain models
    pages/             # Workflow app pages
    services/          # Agent API service and signal store

backend/
  agents/              # Agent prompt, tool loop, provider integration
  tools/               # File, edit, Git, and verification tools
  workflows/           # Persistent workflow/proposal store
  main.py              # FastAPI app
```

## Technology Stack

- Angular 22
- Angular standalone components
- Angular Signals
- Angular Material
- TypeScript 6
- RxJS 7
- SCSS
- FastAPI
- Pydantic
- OpenAI-compatible Python SDK
- OpenRouter
- Vitest through Angular CLI unit-test builder
- ESLint with angular-eslint

## Development

Angular 22 requires Node `^22.22.3`, `^24.15.0`, or `^26.0.0`. If your system Node is older on the same major line, upgrade Node before running Angular CLI commands.

Install dependencies:

```bash
npm install
```

Run the sportsbook app:

```bash
npm start
```

Run the workflow tool:

```bash
npm run start:workflow
```

Run the FastAPI backend:

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

Build:

```bash
npm run build
npm run build:workflow
```

Lint:

```bash
npm run lint
npm run lint:workflow
```

Test:

```bash
npm test
npm run test:workflow
```

## Notes

The Angular CLI commands require a supported Node version. The backend verification tool uses direct TypeScript and ESLint checks so the agent workflow can still validate changes in this local environment.

See [NOTES.md](./NOTES.md) for concise AI-tool and design-decision notes.
