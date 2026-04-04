import discord
from discord.ext import commands
from core.utils import success_embed, warn_embed, error_embed, PURPLE, _get_gif
import logging
import re
import time

log = logging.getLogger("cogs.events")


def _format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m}m {s}s" if s else f"{m}m"
    elif seconds < 86400:
        h, rem = divmod(seconds, 3600)
        m = rem // 60
        return f"{h}h {m}m" if m else f"{h}h"
    else:
        d, rem = divmod(seconds, 86400)
        h = rem // 3600
        return f"{d}d {h}h" if h else f"{d}d"


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Clear AFK if user sends a message
        afk = await self.bot.db.get_afk(message.author.id)
        if afk:
            reason, since = afk[0], afk[1]
            duration = _format_duration(int(time.time()) - since) if since else None
            await self.bot.db.remove_afk(message.author.id)

            desc = f"Welcome back {message.author.mention}! Your AFK has been removed."
            if duration:
                desc += f"\nYou were AFK for: **{duration}**"

            embed = success_embed("AFK Cleared", desc, gif_key="afkremove")
            try:
                await message.channel.send(embed=embed, delete_after=8)
            except (discord.Forbidden, discord.HTTPException):
                pass

        # Notify if an AFK user is mentioned
        for mentioned in message.mentions:
            if mentioned.bot or mentioned.id == message.author.id:
                continue
            user_afk = await self.bot.db.get_afk(mentioned.id)
            if user_afk:
                reason, since = user_afk[0], user_afk[1]
                duration = _format_duration(int(time.time()) - since) if since else None

                embed = discord.Embed(
                    title=f"{mentioned.display_name} is AFK",
                    description=f"**Reason:** {reason}",
                    color=PURPLE
                )
                if duration:
                    embed.add_field(name="AFK for", value=duration, inline=False)
                # Show AFK gif in the mention notification
                gif = _get_gif("afk")
                if gif:
                    embed.set_image(url=gif)
                try:
                    await message.channel.send(embed=embed, delete_after=10)
                except (discord.Forbidden, discord.HTTPException):
                    pass

    @commands.command(name="afk")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def afk(self, ctx, *, reason: str = "AFK"):
        if re.search(r'https?://\S+|www\.\S+|discord\.gg/\S+', reason, re.IGNORECASE):
            return await ctx.send(embed=warn_embed("Invalid Reason", "Links are not allowed as an AFK reason."))
        if len(reason) > 200:
            return await ctx.send(embed=warn_embed("Reason Too Long", "AFK reason must be under 200 characters."))
        await self.bot.db.set_afk(ctx.author.id, ctx.guild.id, reason)
        embed = success_embed("AFK Set", f"You are now AFK.\n**Reason:** {reason}", gif_key="afk")
        await ctx.send(embed=embed)

    @commands.command(name="afkreset")
    async def afkreset(self, ctx):
        afk = await self.bot.db.get_afk(ctx.author.id)
        if not afk:
            return await ctx.send(embed=warn_embed("Not AFK", "You are not currently AFK."))
        reason, since = afk[0], afk[1]
        duration = _format_duration(int(time.time()) - since) if since else None
        await self.bot.db.remove_afk(ctx.author.id)
        desc = "Your AFK status has been removed."
        if duration:
            desc += f"\nYou were AFK for: **{duration}**"
        embed = success_embed("AFK Cleared", desc, gif_key="afkremove")
        await ctx.send(embed=embed)

    @commands.command(name="afkremove")
    @commands.has_permissions(administrator=True)
    async def afkremove(self, ctx, user: discord.Member):
        if ctx.guild.owner != ctx.author and ctx.author.id not in self.bot.owner_ids:
            return await ctx.send(embed=warn_embed("Access Denied", "Only the server owner can use this command."))
        afk = await self.bot.db.get_afk(user.id)
        if not afk:
            return await ctx.send(embed=warn_embed("Not AFK", f"{user.mention} is not currently AFK."))
        await self.bot.db.remove_afk(user.id)
        embed = success_embed("AFK Cleared", f"AFK status removed for {user.mention}.", gif_key="afkremove")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Events(bot))
