from __future__ import annotations

import logging

import discord
from discord.ext.commands import Bot

from ht_manager.bot.permissions import admin_only
from ht_manager.db.repositories import ctfs as ctfs_repo
from ht_manager.services import ctfs as ctfs_service
from ht_manager.services import polls as polls_service

logger = logging.getLogger(__name__)


def register_forcestartctf_command(bot: Bot) -> None:
    @bot.tree.command(
        name="forcestartctf",
        description="Skip the poll and activate a DRAFT CTF directly",
    )
    @admin_only()
    @discord.app_commands.describe(ctf_id="ID of the DRAFT CTF to activate")
    async def forcestartctf(interaction: discord.Interaction, ctf_id: int) -> None:
        await interaction.response.defer()
        client = interaction.client
        settings = client.settings  # type: ignore[attr-defined]
        session_factory = client.session_factory  # type: ignore[attr-defined]

        async with session_factory() as session:
            non_terminal = await ctfs_repo.list_non_terminal(session)
        if non_terminal:
            names = ", ".join(f"{ctf.name} ({ctf.status.value})" for ctf in non_terminal)
            await interaction.followup.send(
                f"A CTF is already in progress: {names}. "
                "Use `/endctf` or `/archivectf` before starting another."
            )
            return

        try:
            await polls_service.force_start(
                session_factory,
                actor_discord_id=interaction.user.id,
                bot=client,
                ctf_id=ctf_id,
                guild_id=settings.discord_guild_id,
                category_id=settings.ctf_category_id,
                retention_days=settings.ctf_resource_retention_days,
            )
        except ctfs_service.CTFNotFoundError as exc:
            await interaction.followup.send(str(exc))
            return
        except polls_service.InvalidPollStateError as exc:
            await interaction.followup.send(str(exc))
            return
        except Exception:
            logger.exception("Force-start failed for ctf_id=%s", ctf_id)
            await interaction.followup.send(
                "Force-start failed — check the logs. It's safe to retry with `/setupctf` "
                "once the underlying issue (permissions, missing channel, etc.) is fixed."
            )
            return

        await interaction.followup.send(
            f"CTF #{ctf_id} is active — no poll was run, so `/addctfmember` its participants."
        )
