# HT-Manager

[![CI](https://github.com/HackerTroupe/HT-Manager/actions/workflows/ci.yml/badge.svg)](https://github.com/HackerTroupe/HT-Manager/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2.svg)](https://discordpy.readthedocs.io/)
![License: All Rights Reserved](https://img.shields.io/badge/license-All%20Rights%20Reserved-red.svg)
[![Status: v1.0](https://img.shields.io/badge/status-v1.0-brightgreen.svg)](CHANGELOG.md)

A Discord bot that runs HackerTroupe's CTF operations end to end: curating
and polling the next CTF from CTFTime, standing up a dedicated Discord
workspace for the winner, tracking who played, and syncing results back
automatically. Single-guild, one active CTF at a time, by design.

The bot and [hackertroupe.dev](https://hackertroupe.dev) are intentionally
independent — no shared API or database.

## Table of contents

- [Features](#features)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Commands](#commands)
- [Architecture](#architecture)
- [Deployment](#deployment)
- [Project status](#project-status)
- [License](#license)

## Features

- **CTF curation** — pulls upcoming events from CTFTime and runs a native Discord poll to pick the next one.
- **Automatic event setup** — the poll winner gets its own Discord role and a dedicated Forum channel, created and torn down automatically.
- **Participation tracking** — records who voted and who was added manually, independent of any Discord role that later gets cleaned up.
- **Result sync** — checks CTFTime for results every 12 hours and announces genuinely new/changed ones; manual corrections are never overwritten by the sync.
- **Audit log** — every admin mutation is recorded with a before/after snapshot.
- **Automatic cleanup** — CTF roles/threads expire on a retention window; finished workspaces move to an archive category a few days after the event ends.

## Quick start

1. Copy `.env.example` to `.env` and fill in real values (Discord bot
   token, guild ID, channel/role IDs, CTFTime team ID). Never commit
   `.env`. See [Configuration](#configuration) for what each value means.
2. Start Postgres and create the app + test databases (the second command
   is safe to re-run; ignore "already exists" if it prints):
   ```bash
   docker compose up -d --wait postgres
   docker compose exec postgres createdb -U ht_manager ht_manager_test
   ```
3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. Run migrations:
   ```bash
   export DATABASE_URL=postgresql+asyncpg://ht_manager:ht_manager@localhost:5432/ht_manager
   alembic upgrade head
   ```
5. Run tests and lint. Tests run against a separate `ht_manager_test`
   database (see step 2) and migrate it automatically; override the target
   with `TEST_DATABASE_URL` if needed. Tests that don't touch the database
   (config, the CTFTime client, permissions, formatting) run without
   Postgres at all, so `pytest tests/test_config.py` works on a bare
   checkout.
   ```bash
   pytest
   ruff check .
   ```
6. Run the bot:
   ```bash
   python -m ht_manager.main
   ```

Or run everything through Compose once `.env` is filled in:

```bash
docker compose up --build
```

## Configuration

Every value lives in `.env` (see `.env.example` for the template); all are
loaded and validated by `Settings` (`src/ht_manager/config.py`).

| Variable | Purpose |
|---|---|
| `DISCORD_TOKEN` | Bot token from the Discord Developer Portal. |
| `DISCORD_GUILD_ID` | The single guild this bot serves. Commands are rejected outside it. |
| `DATABASE_URL` | Postgres connection string for host-side (non-Docker) runs; Compose builds its own from the `POSTGRES_*` values instead. |
| `CTFTIME_TEAM_ID` | The team's numeric CTFTime ID, used to find its row in synced standings. |
| `RESULTS_CHANNEL_ID` | Channel where result announcements are posted. |
| `CTF_CATEGORY_ID` | Category a CTF's dedicated Forum channel is created under. |
| `CTF_ARCHIVE_CATEGORY_ID` | Category a finished CTF's forum is moved into after the archive delay. |
| `ADMIN_ROLE_IDS` | Comma-separated role IDs allowed to run admin commands. |
| `MEMBER_ROLE_ID` | Optional — gates participation commands to members holding this role. |
| `BOT_LOG_CHANNEL_ID` | Optional — private channel for operational warnings. |
| `CTF_RESOURCE_RETENTION_DAYS` | Days before a finished CTF's role is deleted and its post locked. Default `60`. |
| `LOG_LEVEL` | Python logging level. Default `INFO`. |

## Commands

19 slash commands, admin-gated or open depending on what they do. Full
reference with parameters and behavior notes: **[docs/COMMANDS.md](docs/COMMANDS.md)**.

## Architecture

Layered: thin Discord command handlers → domain services (business logic,
no direct `discord.py` imports outside one module) → repositories → models.
Postgres is the source of truth; Discord roles and channels are treated as
disposable. Full write-up, including the CTFTime API quirks this bot works
around: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

## Deployment

Docker Compose is the deployment unit: Postgres + a one-shot migration job
that gates the bot service. Full setup, update, Azure VM notes, and backup
procedure: **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**.

## Project status

v1.0. M0 through M6 and M8 complete: CTF data and CTFTime ingestion,
`/nextctf` polling, event setup (roles/dedicated forum workspace/
participation), retention cleanup, result sync, end-of-CTF summaries, and
production hardening (unprivileged containers, Postgres bound to
localhost, Azure deployment notes, backups). M7 (a read-only website API)
is out of scope — the bot and hackertroupe.dev are intentionally
independent. See [CHANGELOG.md](CHANGELOG.md) for the full history.

## License

All rights reserved — see [LICENSE](LICENSE). This repository is public
for reading and reference; it is not open-source and no license to reuse,
modify, or redistribute the code is granted.
