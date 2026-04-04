import discord
from discord.ext import commands
from core.utils import PURPLE
import logging
import asyncio

log = logging.getLogger("cogs.fun")


def _fun_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(title=title, description=description, color=PURPLE)


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _send_and_cleanup(self, ctx, embed: discord.Embed, delay: int = 8):
        """Send embed then delete both the command message and embed after delay seconds."""
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(delay)
        try:
            await msg.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.command(name="ben")
    async def ben(self, ctx, user: discord.Member = None):
        """Pretend to ban someone (harmless fun)."""
        if user is None:
            return await ctx.send(embed=discord.Embed(
                description="Mention someone to fake ban!",
                color=PURPLE
            ), delete_after=5)
        embed = _fun_embed(
            "Banned",
            f"{user.mention} has been banned by {ctx.author.mention}\n**Reason:** Vibes only."
        )
        await self._send_and_cleanup(ctx, embed)

    @commands.command(name="slap")
    async def slap(self, ctx, user: discord.Member = None):
        if user is None:
            return await ctx.send(embed=discord.Embed(description="Mention someone to slap!", color=PURPLE), delete_after=5)
        embed = _fun_embed("Slap", f"{ctx.author.mention} slapped {user.mention}!")
        await self._send_and_cleanup(ctx, embed)

    @commands.command(name="punch")
    async def punch(self, ctx, user: discord.Member = None):
        if user is None:
            return await ctx.send(embed=discord.Embed(description="Mention someone to punch!", color=PURPLE), delete_after=5)
        embed = _fun_embed("Punch", f"{ctx.author.mention} punched {user.mention}!")
        await self._send_and_cleanup(ctx, embed)

    @commands.command(name="cuddle")
    async def cuddle(self, ctx, user: discord.Member = None):
        if user is None:
            return await ctx.send(embed=discord.Embed(description="Mention someone to cuddle!", color=PURPLE), delete_after=5)
        embed = _fun_embed("Cuddle", f"{ctx.author.mention} is cuddling {user.mention}!")
        await self._send_and_cleanup(ctx, embed)

    @commands.command(name="hug")
    async def hug(self, ctx, user: discord.Member = None):
        if user is None:
            return await ctx.send(embed=discord.Embed(description="Mention someone to hug!", color=PURPLE), delete_after=5)
        embed = _fun_embed("Hug", f"{ctx.author.mention} hugged {user.mention}!")
        await self._send_and_cleanup(ctx, embed)

    @commands.command(name="kiss")
    async def kiss(self, ctx, user: discord.Member = None):
        if user is None:
            return await ctx.send(embed=discord.Embed(description="Mention someone to kiss!", color=PURPLE), delete_after=5)
        embed = _fun_embed("Kiss", f"{ctx.author.mention} kissed {user.mention}!")
        await self._send_and_cleanup(ctx, embed)


async def setup(bot):
    await bot.add_cog(Fun(bot))
