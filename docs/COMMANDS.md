# Command reference

All commands are Discord slash commands. **Admin** means the caller must
hold one of the roles in `ADMIN_ROLE_IDS` and be in the configured guild
(`is_admin()`, enforced by `admin_only()` — see [ARCHITECTURE.md](ARCHITECTURE.md#permissions)).

## CTF lifecycle

| Command | Access | Description |
|---|---|---|
| `/nextctf [window_days] [duration_hours]` | Admin | Fetches upcoming CTFTime events, lets the admin curate candidates, then publishes a native Discord poll. `duration_hours` (1-768, default 48) sets how long the poll stays open. |
| `/resolvepoll` | Admin | Manually picks the winner when a poll ties. |
| `/setupctf <ctf_id>` | Admin | Retries role/workspace creation for a CTF — safe to re-run after a partial failure. |
| `/forcestartctf <ctf_id>` | Admin | Skips the poll: takes a `DRAFT` CTF straight to `ACTIVE` (role + workspace created, but no voters to assign the role to — follow up with `/addctfmember`). Blocks if another CTF is already in progress, same as `/nextctf`. |
| `/addctf <name> <year> <start_at> <end_at> …` | Admin | Adds a CTF to the database as a draft, bypassing the poll flow (private events, backfilling history). |
| `/editctf <ctf_id> …` | Admin | Corrects a CTF's metadata. |
| `/deletectf <ctf_id>` | Admin | Hard-deletes a draft CTF (only drafts — anything with votes or results is kept for history). |
| `/endctf <ctf_id>` | Admin | Finalizes a CTF and posts its summary. |
| `/archivectf <ctf_id>` | Admin | Archives a finished CTF; its forum moves to the archive category 4 days later. |
| `/listctfs` | Everyone | Lists all CTFs, newest first, paginated. |
| `/summary <ctf_id>` | Everyone | Shows a CTF's summary without changing its status. |

## Participation

| Command | Access | Description |
|---|---|---|
| `/addctfmember <ctf_id> <member>` | Admin | Manually records a participant (the DB record, not the Discord role, is what history reads). |
| `/removectfmember <ctf_id> <member>` | Admin | Manually removes a participant record. |
| `/ctfmembers <ctf_id>` | Everyone | Shows recorded participants for a CTF. |
| `/participation <member>` | Everyone | Shows how many CTFs a member has joined. |

## Results

| Command | Access | Description |
|---|---|---|
| `/addresult <ctf_id> …` | Admin | Records a CTF result manually. |
| `/editresult <ctf_id> …` | Admin | Corrects a recorded result; marks it `MANUAL` so the automatic sync won't overwrite it. |
| `/resultsync` | Admin | Runs the CTFTime result sync immediately, instead of waiting for the 12-hour job. |
| `/setcategory <ctf_id> <category> <solved> <total>` | Admin | Sets or corrects one category's solved/total (CTFTime has no per-category breakdown). |

## Other

| Command | Access | Description |
|---|---|---|
| `/ping` | Everyone | Health/latency check. |
