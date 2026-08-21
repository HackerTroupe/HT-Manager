from __future__ import annotations

import discord
from discord.ext.commands import Bot

from ht_manager.bot.permissions import admin_only
from ht_manager.services import ctfs as ctfs_service


def register_clear_command(bot: Bot) -> None:
    @bot.tree.command(name="clear", description="Delete the newest draft CTFs")
    @admin_only()
    @discord.app_commands.describe(count="How many newest draft CTFs to delete")
    async def clear(
        interaction: discord.Interaction,
        count: discord.app_commands.Range[int, 1, 100],
    ) -> None:
        session_factory = interaction.client.session_factory  # type: ignore[attr-defined]
        try:
            async with session_factory() as session, session.begin():
                deleted_ids = await ctfs_service.clear_latest_drafts(
                    session, actor_discord_id=interaction.user.id, count=count
                )
        except (ValueError, ctfs_service.InvalidCTFStateError) as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return

        if not deleted_ids:
            await interaction.response.send_message("There are no draft CTFs to clear.")
            return
        ids = ", ".join(f"#{ctf_id}" for ctf_id in deleted_ids)
        await interaction.response.send_message(f"Cleared newest draft CTFs: {ids}.")