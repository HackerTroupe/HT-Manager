from __future__ import annotations

import logging

import discord
from discord.ext.commands import Bot

from ht_manager.bot.permissions import admin_only
from ht_manager.services import polls as polls_service

logger = logging.getLogger(__name__)


def register_cancelpoll_command(bot: Bot) -> None:
    @bot.tree.command(
        name="cancelpoll",
        description="Cancel the currently open CTF poll before it closes on its own",
    )
    @admin_only()
    async def cancelpoll(interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        client = interaction.client
        session_factory = client.session_factory  # type: ignore[attr-defined]

        try:
            async with session_factory() as session, session.begin():
                poll = await polls_service.cancel_open_poll(
                    session, actor_discord_id=interaction.user.id
                )
        except polls_service.PollNotFoundError as exc:
            await interaction.followup.send(str(exc))
            return

        try:
            channel = client.get_channel(poll.channel_id) or await client.fetch_channel(
                poll.channel_id
            )
            message = await channel.fetch_message(poll.discord_message_id)
            if message.poll is not None:
                await message.poll.end()
        except discord.HTTPException:
            logger.exception("Could not end the Discord poll message for poll_id=%s", poll.id)

        await interaction.followup.send(
            "Poll cancelled — all candidate CTFs were reset. Run `/nextctf` when you're ready "
            "to start a new one."
        )
