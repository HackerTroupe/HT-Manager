from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ht_manager.db.repositories import ctfs as ctfs_repo
from ht_manager.services import ctfs as ctfs_service

START = datetime(2026, 9, 1, tzinfo=UTC)
END = datetime(2026, 9, 3, tzinfo=UTC)


async def _make_ctf(session: AsyncSession, name: str) -> int:
    ctf = await ctfs_service.create_draft(
        session, actor_discord_id=1, name=name, year=2026, start_at=START, end_at=END
    )
    return ctf.id


async def test_list_page_orders_by_id_descending(db_session: AsyncSession) -> None:
    first_id = await _make_ctf(db_session, "First")
    second_id = await _make_ctf(db_session, "Second")

    rows = await ctfs_repo.list_page(db_session, limit=10, offset=0)

    assert [ctf.id for ctf in rows] == [second_id, first_id]


async def test_list_page_respects_limit_and_offset(db_session: AsyncSession) -> None:
    for i in range(3):
        await _make_ctf(db_session, f"CTF {i}")

    first_page = await ctfs_repo.list_page(db_session, limit=2, offset=0)
    second_page = await ctfs_repo.list_page(db_session, limit=2, offset=2)

    assert len(first_page) == 2
    assert len(second_page) == 1


async def test_count_matches_number_of_ctfs(db_session: AsyncSession) -> None:
    assert await ctfs_repo.count(db_session) == 0
    await _make_ctf(db_session, "Only one")
    assert await ctfs_repo.count(db_session) == 1
