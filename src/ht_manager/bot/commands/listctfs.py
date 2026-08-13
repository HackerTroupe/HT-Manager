from __future__ import annotations

import discord
from discord.ext.commands import Bot

from ht_manager.db.repositories import ctfs as ctfs_repo

PAGE_SIZE = 10


def _format_page(rows: list, page: int, total_pages: int) -> str:
    if not rows:
        return "No CTFs recorded yet."
    lines = [f"#{ctf.id} {ctf.name} ({ctf.year}) — {ctf.status.value}" for ctf in rows]
    return f"CTFs (page {page}/{total_pages}):\n" + "\n".join(lines)


class ListCtfsView(discord.ui.View):
    def __init__(self, *, session_factory, page: int, total: int) -> None:
        super().__init__(timeout=300)
        self.session_factory = session_factory
        self.page = page
        self.total = total
        self._update_buttons()

    @property
    def total_pages(self) -> int:
        return max(1, -(-self.total // PAGE_SIZE))

    def _update_buttons(self) -> None:
        self.previous_button.disabled = self.page <= 1
        self.next_button.disabled = self.page >= self.total_pages

    async def _render(self, interaction: discord.Interaction) -> None:
        async with self.session_factory() as session:
            rows = await ctfs_repo.list_page(
                session, limit=PAGE_SIZE, offset=(self.page - 1) * PAGE_SIZE
            )
        self._update_buttons()
        await interaction.response.edit_message(
            content=_format_page(rows, self.page, self.total_pages), view=self
        )

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.page -= 1
        await self._render(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.page += 1
        await self._render(interaction)


def register_listctfs_command(bot: Bot) -> None:
    @bot.tree.command(name="listctfs", description="List all CTFs, most recent first")
    async def listctfs(interaction: discord.Interaction) -> None:
        session_factory = interaction.client.session_factory  # type: ignore[attr-defined]
        async with session_factory() as session:
            total = await ctfs_repo.count(session)
            rows = await ctfs_repo.list_page(session, limit=PAGE_SIZE, offset=0)

        view = ListCtfsView(session_factory=session_factory, page=1, total=total)
        await interaction.response.send_message(
            content=_format_page(rows, 1, view.total_pages), view=view
        )
