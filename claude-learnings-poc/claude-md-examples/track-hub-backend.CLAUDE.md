# Track Hub — Backend

FastAPI + Postgres API for the Track Hub personal work tracker. Built to
eventually replace the frontend's (`track-hub-ui`, separate repo, sibling
directory) `localStorage` persistence — that integration hasn't happened
yet; this API currently runs standalone.

## Stack

- Python + FastAPI
- PostgreSQL via Docker Compose
- SQLAlchemy (2.0-style, `Mapped[...]`) + Alembic for migrations
- No auth, no entry editing, no deployment config — intentionally out of
  scope for now

## Non-default ports — read before assuming 5432/8000

This machine already runs other unrelated Docker containers on the usual
defaults. To avoid collisions:

- Postgres is exposed on host port **5433**, not 5432 (`docker-compose.yml`,
  `.env.example`)
- The API listens on port **8001**, not 8000

Always verify with `127.0.0.1:8001`, not `localhost:8001` — on this
machine `localhost` can resolve to a different service via IPv6/WSL
forwarding.

## Structure

- `app/main.py` — FastAPI app, CORS locked to `http://localhost:5173`
  (the frontend dev server), `/health` endpoint
- `app/database.py` — engine/session setup, `Base`, `get_db` dependency
- `app/config.py` — `Settings`, reads `DATABASE_URL`/`PORT` from `.env`
- `app/enums.py` — `EntryType` (shared between the SQLAlchemy model and
  Pydantic schemas — keep it that way, don't duplicate the enum)
- `app/models/entry.py` — the `Entry` table (UUID pk, `entry_type` Postgres
  enum, `tags` as a Postgres array, `created_at` timestamptz)
- `app/schemas/entry.py` — `EntryCreate` / `EntryResponse`
- `app/routers/entries.py` — `GET/POST /api/entries` (list + `?type=`
  filter, create), `DELETE /api/entries/{id}`
- `alembic/` — migrations; `env.py` is wired to import `app.database.Base`
  and `app.models` directly, and pulls `DATABASE_URL` from `app.config`
  rather than `alembic.ini`

## Commands

```bash
docker compose up -d              # Postgres on 5433
venv\Scripts\activate              # or: source venv/Scripts/activate
alembic upgrade head
uvicorn app.main:app --reload --port 8001
```

New migration after a model change:

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

**No test suite is configured yet.** If a skill/hook asks to "run the full
test suite," there isn't one — say so explicitly rather than assuming a
command exists.

## Conventions

- SQLAlchemy 2.0 typed style (`Mapped[X]` / `mapped_column`), not the
  legacy `Column(...)` declarative style.
- Keep `EntryType` defined once in `app/enums.py` and imported everywhere
  else — don't redefine it in the model or schema.

## Git / GitHub workflow

Governed by the device-wide `github-workflow` skill
(`~/.claude/skills/github-workflow/`) — branch model is
`feature → dev → qa → uat → main`, Conventional Commits, no Claude/Anthropic
attribution in commit messages. See that skill for the full rules; don't
duplicate them here.
