# Architecture

## Layers

```
src/ht_manager/
├── bot/            # discord.py only lives here (+ services/discord_resources.py)
│   ├── commands/   # thin: parse interaction, call a service, format reply
│   └── permissions.py
├── services/       # business logic, one module per domain, never imports discord.py directly
├── jobs/           # scheduled background jobs (APScheduler)
├── db/
│   ├── models/     # SQLAlchemy models
│   └── repositories/  # data access; no business rules
└── config.py       # Settings (pydantic-settings)
```

Each service owns a fixed, non-overlapping domain: `ctfs.py` (CTF
metadata), `ctftime.py` (the CTFTime HTTP client, isolated so its
instability can't leak into the rest of the app), `polls.py` (poll
lifecycle and winner selection), `participation.py` (who played),
`discord_resources.py` (the **only** module allowed to call `discord.py`
directly — role/forum/channel operations), `results.py` (result
persistence and dedup).

## Design decisions

**Discord is a presentation layer; Postgres is the source of truth.**
Participation and result records never use Discord IDs as primary keys.
Roles and forum posts are temporary and admin-deletable — the historical
record has to outlive them. A CTF's role can be manually deleted or a
forum archived without losing who played or what the result was.

**No event bus.** Cross-service sequences (e.g. resolving a poll winner —
create a role, stand up a forum, record participation, activate the CTF)
are explicit, ordered function calls, not pub/sub. Each step is
checkpointed independently: if step 3 of 4 fails, a retry re-checks state
and only does what's still missing, rather than either replaying
everything or leaving orphaned Discord resources nothing tracks.

**Transaction ownership is fixed.** Repositories and services never call
`session.commit()`/`session.rollback()` — the caller owns the unit of
work. Multi-step sequences that call out to the Discord API deliberately
do *not* hold one transaction open across the whole sequence — a Discord
API call can be slow or fail independently of the database, and holding a
transaction across it would block other work for no reason.

**Migrations are one-way documents.** Once an Alembic migration is
applied anywhere, it's never edited — a new migration follows. CI runs
`alembic upgrade head && alembic downgrade base && alembic upgrade head &&
alembic check` on every push, so a migration that can't reverse cleanly,
or that's drifted from the models, fails the build immediately rather than
surfacing as a 3am production surprise.

**Single guild, one active CTF at a time.** Both are deliberate scope
cuts, not gaps. There's no multi-tenancy and no concurrent-CTF handling
anywhere in the codebase.

## Permissions

`admin_only()` (`bot/permissions.py`) is an `app_commands.check` decorator
applied directly under `@tree.command`, so a permission denial raises
`CheckFailure` uniformly and is handled in one place
(`HTManagerBot._on_app_command_error`) rather than scattered `if` checks
inside handlers. `is_admin()` checks both role membership
(`ADMIN_ROLE_IDS`) and that the interaction is happening in the configured
guild (`DISCORD_GUILD_ID`).

## CTFTime integration notes

Verified against the live API, not the docs:

- There is no per-event results endpoint. Results are published per
  *year*: `/api/v1/results/<year>/`, keyed by event ID as a string, with
  standings under `scores` and `points` serialized as a string.
- `points` is that event's score, not the team's global CTFTime rating —
  it maps to `Result.score`.
- The result-sync job groups its candidates by year and makes one request
  per year (not one per CTF) — one year of data covers every event and is
  a few megabytes, so a per-CTF request pattern would be both slower and
  needlessly repetitive.
