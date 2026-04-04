import discord
from discord.ext import commands
from core.utils import log_action, success_embed, error_embed, warn_embed, mod_embed
import logging

log = logging.getLogger("cogs.voice")


class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── Auto-enforce VC bans ───────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Kick a VC-banned member as soon as they join any voice channel."""
        # Only act when someone joins a channel
        if after.channel is None:
            return
        if before.channel is not None and before.channel.id == after.channel.id:
            return  # Same channel (mute/deafen change), not a join
        try:
            is_banned = await self.bot.db.is_vcbanned(member.guild.id, member.id)
        except Exception as e:
            log.warning("is_vcbanned lookup failed for %s: %s", member, e)
            return
        if is_banned:
            try:
                await member.move_to(None, reason="VC banned")
            except (discord.Forbidden, discord.HTTPException) as e:
                log.warning("Could not enforce vcban on %s: %s", member, e)
                return
            try:
                await member.send(embed=warn_embed(
                    "VC Banned",
                    f"You are banned from voice channels in **{member.guild.name}**."
                ))
            except (discord.Forbidden, discord.HTTPException):
                pass

    # ── VCBAN ─────────────────────────────────────────────────────────────────
    @commands.command(name="vcban")
    @commands.has_permissions(administrator=True)
    async def vcban(self, ctx, user: discord.Member = None, *, reason: str = "No reason provided"):
        """Permanently ban a member from all voice channels."""
        if not user:
            return await ctx.send(embed=error_embed("Missing User", "Usage: `!vcban <user> [reason]`"))
        await self.bot.db.add_vcban(ctx.guild.id, user.id)
        if user.voice:
            try:
                await user.move_to(None, reason=reason)
            except Exception:
                pass
        embed = mod_embed("VC Ban Applied", f"{user.mention} has been banned from voice channels.")
        embed.add_field(name="User",      value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention,              inline=True)
        embed.add_field(name="Reason",    value=reason,                          inline=False)
        await ctx.send(embed=embed)
        await log_action(self.bot, ctx.guild, "VCBan", user, ctx.author, reason)

    # ── VCUNBAN ───────────────────────────────────────────────────────────────
    @commands.command(name="vcunban")
    @commands.has_permissions(administrator=True)
    async def vcunban(self, ctx, user: discord.Member = None):
        """Revoke a voice channel ban."""
        if not user:
            return await ctx.send(embed=error_embed("Missing User", "Usage: `!vcunban <user>`"))
        is_banned = await self.bot.db.is_vcbanned(ctx.guild.id, user.id)
        if not is_banned:
            return await ctx.send(embed=error_embed("Not VC Banned", f"{user.mention} does not have a VC ban."))
        await self.bot.db.remove_vcban(ctx.guild.id, user.id)
        embed = mod_embed("VC Ban Removed", f"{user.mention} can now join voice channels.")
        embed.add_field(name="User",      value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention,              inline=True)
        await ctx.send(embed=embed)
        await log_action(self.bot, ctx.guild, "VCUnban", user, ctx.author, "VC ban removed")

    # ── VCKICK ────────────────────────────────────────────────────────────────
    @commands.command(name="vckick")
    @commands.has_permissions(move_members=True)
    async def vckick(self, ctx, user: discord.Member = None, *, reason: str = "No reason provided"):
        """Remove a member from their current voice channel."""
        if not user:
            return await ctx.send(embed=error_embed("Missing User", "Usage: `!vckick <user> [reason]`"))
        if not user.voice or not user.voice.channel:
            return await ctx.send(embed=error_embed("Not in VC", f"{user.mention} is not in a voice channel."))
        channel_name = user.voice.channel.name
        await user.move_to(None, reason=reason)
        embed = mod_embed("VC Kick", f"{user.mention} has been removed from **{channel_name}**.")
        embed.add_field(name="User",      value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention,              inline=True)
        embed.add_field(name="Reason",    value=reason,                          inline=False)
        await ctx.send(embed=embed)
        await log_action(self.bot, ctx.guild, "VCKick", user, ctx.author, reason)

    # ── VCMOVEALL ─────────────────────────────────────────────────────────────
    @commands.command(name="vcmoveall")
    @commands.has_permissions(move_members=True)
    async def vcmoveall(self, ctx, destination: str = None, *, source: str = None):
        """Move all members from source VC to destination.
        Usage: !vcmoveall <destination> [source]"""
        if not destination:
            return await ctx.send(embed=error_embed(
                "Missing Destination",
                "Usage: `!vcmoveall <destination_channel> [source_channel]`\n"
                "Use a channel mention, name, or ID."
            ))

        # Resolve destination
        dest_channel = await self._resolve_vc(ctx.guild, destination)
        if not dest_channel:
            return await ctx.send(embed=error_embed(
                "Channel Not Found",
                f"Could not find a voice channel matching `{destination}`."
            ))

        # Resolve source
        members = []
        source_name = "all voice channels"
        if source:
            src_channel = await self._resolve_vc(ctx.guild, source)
            if not src_channel:
                return await ctx.send(embed=error_embed("Source Not Found", f"Could not find source channel `{source}`."))
            members = [m for m in src_channel.members if m != ctx.guild.me]
            source_name = src_channel.name
        elif ctx.author.voice and ctx.author.voice.channel:
            members = [m for m in ctx.author.voice.channel.members if m != ctx.guild.me]
            source_name = ctx.author.voice.channel.name
        else:
            for vc in ctx.guild.voice_channels:
                if vc != dest_channel:
                    members.extend([m for m in vc.members if m != ctx.guild.me])

        if not members:
            return await ctx.send(embed=error_embed("No Members", "There are no members to move."))

        moved = 0
        for member in members:
            try:
                await member.move_to(dest_channel, reason=f"VCMoveAll by {ctx.author}")
                moved += 1
            except Exception:
                pass

        embed = mod_embed("VC Move All", f"Moved **{moved}** member(s) from **{source_name}** to {dest_channel.mention}.")
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)
        await log_action(self.bot, ctx.guild, "VCMoveAll", None, ctx.author,
                         f"Moved {moved} members from {source_name} to {dest_channel.name}")

    async def _resolve_vc(self, guild: discord.Guild, query: str):
        """Find a VoiceChannel by mention, ID, or name."""
        clean = query.strip().strip("<#>")
        try:
            ch = guild.get_channel(int(clean))
            if ch and isinstance(ch, discord.VoiceChannel):
                return ch
        except ValueError:
            pass
        return discord.utils.find(
            lambda c: isinstance(c, discord.VoiceChannel) and c.name.lower() == clean.lower(),
            guild.channels
        )

    # ── ADDUSER ───────────────────────────────────────────────────────────────
    @commands.command(name="adduser")
    @commands.has_permissions(manage_channels=True)
    async def adduser(self, ctx, user: discord.Member = None, channel: discord.TextChannel = None):
        """Grant a member read and send access to a channel."""
        if not user:
            return await ctx.send(embed=error_embed("Missing User", "Usage: `!adduser <user> [channel]`"))
        channel = channel or ctx.channel
        await channel.set_permissions(user, read_messages=True, send_messages=True)
        embed = mod_embed("User Added", f"{user.mention} can now access {channel.mention}.")
        embed.add_field(name="User",      value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="Channel",   value=channel.mention,                 inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention,              inline=True)
        await ctx.send(embed=embed)
        await log_action(self.bot, ctx.guild, "AddUser", user, ctx.author, f"Added {user} to #{channel.name}")


async def setup(bot):
    await bot.add_cog(Voice(bot))
