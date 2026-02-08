from __future__ import annotations

import logging

import discord
from discord.ext import commands


logger = logging.getLogger(__name__)


async def sync_commands(bot: commands.Bot, dev_guild_id: int | None) -> None:
    if dev_guild_id:
        await bot.tree.sync(guild=discord.Object(id=dev_guild_id))
        logger.info("Synced slash commands to dev guild %s", dev_guild_id)
        return

    await bot.tree.sync()
    logger.info("Synced slash commands globally")
