# HT-Manager

Discord bot for HackerTroupe's CTF operations: curating and polling the next
CTF, tracking participation, and syncing/announcing CTFTime results.

## Local development

1. Copy `.env.example` to `.env` and fill in real values (Discord bot
   token, guild ID, channel/role IDs, CTFTime team ID). Never commit `.env`.
2. Start Postgres and create the app + test databases (the second command is
   safe to re-run; ignore "already exists" if it prints):
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
   (config, the CTFTime client, permissions, formatting) run without Postgres
   at all, so `pytest tests/test_config.py` works on a bare checkout.
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

## Deploying

Compose is the deployment unit — one small VM running Postgres and the bot
side by side. `docker compose up -d --build` brings up Postgres, runs
`alembic upgrade head` as a one-shot migration job, and only then starts
the bot.

Before deploying:

- Fill in `.env` from `.env.example` and **change `POSTGRES_PASSWORD`** —
  the default is a local-development convenience.
- Postgres publishes only to `127.0.0.1`, and the bot/migrate containers run
  as an unprivileged user. Both are deliberate; don't widen them without a
  reason.
- The bot restarts automatically (`restart: unless-stopped`); the migration
  job intentionally does not.

Check on it with `docker compose logs -f ht-manager-bot`. The CTFTime result
sync records its health in the `sync_state` table — `last_success_at` only
advances on a fully clean run, and `last_error` holds the last failure.

### Azure VM specifics

The bot only makes outbound connections (Discord gateway, CTFTime, its own
Postgres container) — it doesn't serve HTTP. The VM's Network Security Group
needs no inbound rule beyond SSH; don't open 5432 or anything else inbound.

1. Install Docker Engine + the Compose plugin on the VM (Azure's Ubuntu
   images don't ship it — follow Docker's official install steps for the
   distro, not the Snap package, which has known Compose-plugin issues).
2. Clone the repo, `cp .env.example .env` and fill it in (see below), set a
   real `POSTGRES_PASSWORD`.
3. `docker compose up -d --build`.
4. Confirm `restart: unless-stopped` is enough for your needs — it survives
   container crashes and `docker` daemon restarts, but a full VM
   deallocate/reallocate (e.g. an Azure for Students credit-triggered
   shutdown) needs the Docker daemon itself enabled at boot
   (`systemctl enable docker`, on by default on Azure's Ubuntu images).

### Backups

The only durable state is the `ht_manager_postgres_data` volume — Discord
roles/forums are disposable by design (spec §8), so backups only need to
cover Postgres. Ad hoc dump:

```bash
docker compose exec postgres pg_dump -U ht_manager ht_manager > backup-$(date +%F).sql
```

For unattended backups, cron the same command on the host (outside the
container) and rotate old dumps; there's no in-repo backup job, so this is
an operational step you own on the deployment VM. Restore with:

```bash
cat backup-2026-08-12.sql | docker compose exec -T postgres psql -U ht_manager ht_manager
```

## Commands

Admin-only unless noted: `/addctf`, `/editctf`, `/deletectf`, `/nextctf`,
`/resolvepoll`, `/setupctf`, `/addctfmember`, `/removectfmember`,
`/addresult`, `/editresult`, `/resultsync`, `/setcategory`, `/endctf`,
`/archivectf`. Open to everyone: `/ping`, `/ctfmembers`, `/listctfs`,
`/participation`, `/summary`.

## Project status

v1.0. M0 through M6 and M8 complete: CTF data and CTFTime ingestion,
`/nextctf` polling, event setup (roles/dedicated forum workspace/
participation), retention cleanup, result sync, end-of-CTF summaries, and
production hardening (unprivileged containers, Postgres bound to localhost,
Azure deployment notes, backups). M7 (a read-only website API) is out of
scope — the bot and hackertroupe.dev are intentionally independent. See
`CHANGELOG.md` for details.
