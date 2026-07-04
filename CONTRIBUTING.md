# Contributing to Vachan.ai

Thanks for helping make Vachan.ai better. This guide covers how to set up the project locally, keep commits and branches tidy, and open a pull request.

## Local development setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/abhisheksharma001/Vachan-ai.git
   cd Vachan.ai
   ```

2. **Start backing services**
   ```bash
   docker compose up -d
   ```
   This starts Postgres (with pgvector) and Redis.

3. **Backend**
   ```bash
   cd backend
   python3 -m venv .venv
   ./.venv/bin/pip install -r requirements.txt
   ./.venv/bin/python -m spacy download en_core_web_sm
   ./.venv/bin/alembic upgrade head
   ./.venv/bin/uvicorn app.main:app --reload --port 8000
   ```

4. **Frontend**
   ```bash
   cd frontend
   npm install
   cp .env.example .env.local
   npm run dev
   ```
   The app runs at `http://localhost:3000` and talks to the backend at `http://127.0.0.1:8000`.

5. **Environment**
   - Copy `.env.example` to `.env` in the repo root.
   - Local dev works without API keys.
   - Set `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, etc. only when you want live LLM features.

See [`backend/README.md`](backend/README.md) and [`docs/02_ARCHITECTURE.md`](docs/02_ARCHITECTURE.md) for deeper context.

## Branch naming

Use one of these prefixes:

- `feature/` — new capability
- `fix/` — bug fix
- `docs/` — documentation or README changes
- `chore/` — tooling, deps, config

Example: `feature/tonality-sliders`, `fix/persona-cache-key`.

## Commit messages

Conventional Commits are preferred:

```
feat: add fidelity ring component
fix: preserve scroll position on conversation switch
docs: update architecture diagram
chore: bump @tanstack/react-query
```

Keep the first line under 72 characters. Add body paragraphs for non-obvious changes.

## Tests

Run the backend test suite:

```bash
cd backend
./.venv/bin/python -m pytest
```

Build the frontend to catch type and build errors:

```bash
cd frontend
npm run build
```

## Code style

- **Python**: follow PEP 8, use type hints where reasonable, keep functions small and async-friendly.
- **TypeScript / React**: prefer explicit types, colocate hooks and components, and use the existing `cn()` utility for class names.
- **Tailwind**: use the design tokens in `frontend/app/globals.css` (`sand-*`, `coral-*`, `ink-*`) instead of hardcoded hex values.
- **No secrets in code**. Use environment variables and never commit `.env` files.

## Pull request process

1. Open a PR from your branch to `main`.
2. Fill out the PR template.
3. Make sure checks pass (`pytest`, `npm run build`, `next lint`).
4. Request review from a maintainer.
5. Address feedback and squash fixup commits if asked.
6. A maintainer will merge once approved.

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). Be respectful, constructive, and inclusive.
