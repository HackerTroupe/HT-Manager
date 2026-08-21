from __future__ import annotations

import discord
from discord.ext.commands import Bot

from ht_manager.bot.permissions import admin_only
from ht_manager.services import ctfs as ctfs_service


def register_changestate_command(bot: Bot) -> None:
    @bot.tree.command(
        name="changestate", description="Restore a cancelled CTF to draft status"
    )
    @admin_only()
    @discord.app_commands.describe(ctf_id="ID of the cancelled CTF to restore")
    async def changestate(interaction: discord.Interaction, ctf_id: int) -> None:
        session_factory = interaction.client.session_factory  # type: ignore[attr-defined]
        try:
            async with session_factory() as session, session.begin():
                await ctfs_service.restore_cancelled_draft(
                    session, actor_discord_id=interaction.user.id, ctf_id=ctf_id
                )
        except (ctfs_service.CTFNotFoundError, ctfs_service.InvalidCTFStateError) as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return

        await interaction.response.send_message(f"CTF #{ctf_id} restored to draft.")