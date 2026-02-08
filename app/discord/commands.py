from __future__ import annotations

from discord.ext import commands
import discord

from app.db.repo import Repository


def register_admin_commands(bot: commands.Bot, repo: Repository) -> None:
    @bot.command(name="sethub")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def set_hub(ctx: commands.Context, channel: discord.VoiceChannel | None = None) -> None:
        target = channel
        if target is None:
            if ctx.author.voice and ctx.author.voice.channel:
                if isinstance(ctx.author.voice.channel, discord.VoiceChannel):
                    target = ctx.author.voice.channel
            if target is None:
                await ctx.send("Provide a voice channel or join one first.")
                return

        repo.add_hub_channel(ctx.guild.id, target.id, ctx.author.id)
        await ctx.send(f"Hub set: {target.mention}")

    @bot.command(name="unsethub")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def unset_hub(ctx: commands.Context, channel: discord.VoiceChannel) -> None:
        removed = repo.remove_hub_channel(ctx.guild.id, channel.id)
        if removed:
            await ctx.send(f"Hub removed: {channel.mention}")
        else:
            await ctx.send("That channel is not a hub.")

    @bot.command(name="settempcategory")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def set_temp_category(ctx: commands.Context, category: discord.CategoryChannel) -> None:
        repo.set_temp_category(ctx.guild.id, category.id)
        await ctx.send(f"Temp voice category set: {category.name}")

    @bot.command(name="cleartempcategory")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def clear_temp_category(ctx: commands.Context) -> None:
        repo.set_temp_category(ctx.guild.id, None)
        await ctx.send("Temp voice category cleared. Hub category fallback will be used.")

    @bot.command(name="listhubs")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def list_hubs(ctx: commands.Context) -> None:
        hub_ids = repo.list_hub_channels(ctx.guild.id)
        if not hub_ids:
            await ctx.send("No hubs configured.")
            return

        rendered = []
        for hub_id in hub_ids:
            channel = ctx.guild.get_channel(hub_id)
            rendered.append(channel.mention if channel else f"(missing) {hub_id}")

        await ctx.send("Hubs: " + ", ".join(rendered))

    @set_hub.error
    @unset_hub.error
    @set_temp_category.error
    @clear_temp_category.error
    @list_hubs.error
    async def admin_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need Manage Server permission for this command.")
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send("Invalid channel/category argument.")
            return
        raise error
