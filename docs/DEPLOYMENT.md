# Deployment

Compose is the deployment unit — one small VM running Postgres and the bot
side by side. `docker compose up -d --build` brings up Postgres, runs
`alembic upgrade head` as a one-shot migration job, and only then starts
the bot (`ht-manager-bot` depends on the migration job completing
successfully).

## Before deploying

- Copy `.env.example` to `.env` and fill it in — see the [`.env` reference](../README.md#configuration) in the README.
- **Change `POSTGRES_PASSWORD`** — the default in `.env.example` is a local-development convenience, not safe for anything reachable from outside your machine.
- Postgres publishes only to `127.0.0.1`, and the bot/migrate containers run as an unprivileged user. Both are deliberate; don't widen them without a reason.
- The bot restarts automatically (`restart: unless-stopped`); the one-shot migration job intentionally does not.

## Deploying

```bash
git clone <repo-url>
cd HT-Manager
cp .env.example .env   # fill in real values
docker compose up -d --build
```

Check on it with:

```bash
docker compose logs -f ht-manager-bot
```

The CTFTime result sync records its own health in the `sync_state` table —
`last_success_at` only advances on a fully clean run, and `last_error`
holds the last failure, so a stuck sync is visible without digging through
logs.

## Updating a running deployment

```bash
git pull
docker compose up -d --build
```

This rebuilds the bot image, re-runs the migration job (a no-op if there's
nothing new to migrate), and restarts only `ht-manager-bot` — Postgres and
its data volume are untouched. If a migration is involved, check
`docker compose logs ht-manager-migrate` specifically: a failed migration
blocks the bot from starting at all, by design.

## Azure VM specifics

The bot only makes outbound connections (Discord gateway, CTFTime, its own
Postgres container) — it doesn't serve HTTP. The VM's Network Security
Group needs no inbound rule beyond SSH; don't open `5432` or anything else
inbound.

1. Install Docker Engine + the Compose plugin on the VM (Azure's Ubuntu
   images don't ship it — follow Docker's official install steps for the
   distro, not the Snap package, which has known Compose-plugin issues).
2. Clone the repo, `cp .env.example .env` and fill it in, set a real
   `POSTGRES_PASSWORD`.
3. `docker compose up -d --build`.
4. Confirm `restart: unless-stopped` is enough for your needs — it
   survives container crashes and `docker` daemon restarts, but a full VM
   deallocate/reallocate (e.g. an Azure for Students credit-triggered
   shutdown) needs the Docker daemon itself enabled at boot
   (`systemctl enable docker`, on by default on Azure's Ubuntu images).

## Backups

The only durable state is the `ht_manager_postgres_data` volume — Discord
roles/forums are disposable by design, so backups only need to cover
Postgres.

Ad hoc dump:

```bash
docker compose exec postgres pg_dump -U ht_manager ht_manager > backup-$(date +%F).sql
```

For unattended backups, cron the same command on the host (outside the
container) and rotate old dumps — there's no in-repo backup job, so this
is an operational step you own on the deployment VM.

Restore:

```bash
cat backup-2026-08-12.sql | docker compose exec -T postgres psql -U ht_manager ht_manager
```
