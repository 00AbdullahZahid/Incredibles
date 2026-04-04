import discord
from discord.ext import commands
from core.utils import (
    hierarchy_check, log_action,
    mod_embed, error_embed, warn_embed, success_embed,
    has_allowed_role, parse_duration, PINK, YELLOW, PURPLE
)
import datetime
import logging

log = logging.getLogger("cogs.moderation")


async def _is_privileged(ctx) -> bool:
    if ctx.author == ctx.guild.owner or ctx.author.id in ctx.bot.owner_ids:
        return True
    return await has_allowed_role(ctx)


async def _deny_and_alert(ctx, command_name: str):
    """Shown when someone WITHOUT permission tries a mod command."""
    await ctx.send(embed=error_embed(
        "Access Denied",
        f"You do not have permission to use `!{command_name}`.\nThis attempt has been flagged and staff have been notified.",
        gif_key="error"
    ))
    staff_role = discord.utils.find(
        lambda r: any(kw in r.name.lower() for kw in ("staff", "mod", "admin", "team")),
        ctx.guild.roles
    )
    log_ch = await ctx.bot.db.get_log_ban(ctx.guild.id)
    channel = ctx.guild.get_channel(log_ch) if log_ch else None
    if channel:
        alert = error_embed(
            "Unauthorized Command Attempt",
            f"{ctx.author.mention} (`{ctx.author.id}`) tried to use `!{command_name}` without permission.\n"
            f"**Channel:** {ctx.channel.mention}"
        )
        content = staff_role.mention if staff_role else None
        try:
            await channel.send(content=content, embed=alert)
        except Exception:
            pass


def _no_perm_embed():
    """Silent yellow embed with error gif for unprivileged users."""
    return error_embed(
        "Access Denied",
        "You do not have the required role to use this command.",
        gif_key="error"
    )


def _usage_embed(title: str, usage: str):
    """Yellow embed with error gif for incomplete/wrong usage."""
    return error_embed(title, usage, gif_key="error")


class DelWarnSelect(discord.ui.Select):
    def __init__(self, bot, guild, user, warns):
        self.bot = bot
        self.guild = guild
        self.target_user = user
        options = []
        for case_id, mod_id, reason, ts in warns:
            mod = guild.get_member(mod_id)
            mod_name = mod.display_name if mod else str(mod_id)
            label = (reason[:97] + "...") if len(reason) > 100 else reason
            options.append(discord.SelectOption(
                label=label, value=str(case_id), description="Mod: " + mod_name
            ))
        super().__init__(placeholder="Select a warning to delete...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("You need Manage Messages permission.", ephemeral=True)
        case_id = int(self.values[0])
        await self.bot.db.delete_case(case_id)
        embed = mod_embed("Warning Deleted", f"Case `#{case_id}` has been removed from {self.target_user.mention}.", gif_key="delwarn")
        await interaction.response.edit_message(embed=embed, view=None)


class DelWarnView(discord.ui.View):
    def __init__(self, bot, guild, user, warns):
        super().__init__(timeout=60)
        self.add_item(DelWarnSelect(bot, guild, user, warns))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        return True

    async def _dm(self, user, embed):
        try:
            await user.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

    # ── BAN ───────────────────────────────────────────────────────────────────
    @commands.command(name="ban")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def ban(self, ctx, user: discord.Member = None, *, reason: str = "No reason provided"):
        # Permission check FIRST — before anything else
        privileged = await _is_privileged(ctx)
        if not privileged:
            return await ctx.send(embed=error_embed(
                "Access Denied",
                "You do not have permission to use this command.",
                gif_key="error"
            ))
        if user is None:
            return await ctx.send(embed=_usage_embed(
                "Missing User",
                "Usage: `!ban <user> [reason]`"
            ))
        if user.id in (ctx.author.id, ctx.guild.owner.id):
            return await ctx.send(embed=_usage_embed("Permission Denied", "You cannot ban this user."))
        try:
            await hierarchy_check(ctx, user)
        except commands.CheckFailure:
            return
        await self.bot.db.add_case(ctx.guild.id, user.id, ctx.author.id, "Ban", reason)
        dm_embed = mod_embed("You Have Been Banned", f"You were banned from **{ctx.guild.name}**.", gif_key="ban")
        dm_embed.add_field(name="Reason", value=reason)
        await self._dm(user, dm_embed)
        await ctx.guild.ban(user, reason=reason)
        embed = mod_embed("Ban Executed", f"**{user}** has been banned.", gif_key="ban")
        embed.add_field(name="User",      value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention,              inline=True)
        embed.add_field(name="Reason",    value=reason,                          inline=False)
        await ctx.send(embed=embed)
        await log_action(self.bot, ctx.guild, "Ban", user, ctx.author, reason)

    # ── UNBAN ─────────────────────────────────────────────────────────────────
    @commands.command(name="unban")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def unban(self, ctx, user_id: int = None, *, reason: str = "No reason provided"):
        privileged = await _is_privileged(ctx)
        if not privileged:
            return await ctx.send(embed=error_embed(
                "Access Denied",
                "You do not have permission to use this command.",
                gif_key="error"
            ))
        if user_id is None:
            return await ctx.send(embed=_usage_embed(
                "Missing User ID",
                "Usage: `!unban <user_id> [reason]`"
            ))
        try:
            await ctx.guild.unban(discord.Object(id=user_id), reason=reason)
        except discord.NotFound:
            return await ctx.send(embed=_usage_embed("Not Banned", "That user ID is not in the ban list."))
        try:
            user = await self.bot.fetch_user(user_id)
        except Exception:
            user = None
        await self.bot.db.add_case(ctx.guild.id, user_id, ctx.author.id, "Unban", reason)
        embed = mod_embed("Unban Executed", f"User `{user or user_id}` has been unbanned.", gif_key="unban")
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason",    value=reason,              inline=True)
        await ctx.send(embed=embed)
        await log_action(self.bot, ctx.guild, "Unban", user, ctx.author, reason)

    # ── KICK ──────────────────────────────────────────────────────────────────
    @commands.command(name="kick")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def kick(self, ctx, user: discord.Member = None, *, reason: str = "No reason provided"):
        privileged = await _is_privileged(ctx)
        if not privileged:
            return await ctx.send(embed=error_embed(
                "Access Denied",
                "You do not have permission to use this command.",
                gif_key="error"
            ))
        if user is None:
            return await ctx.send(embed=_usage_embed(
                "Missing User",
                "Usage: `!kick <user> [reason]`"
            ))
        if user.id in (ctx.author.id, ctx.guild.owner.id):
            return await ctx.send(embed=_usage_embed("Permission Denied", "You cannot kick this user."))
        try:
            await hierarchy_check(ctx, user)
        except commands.CheckFailure:
            return
        await self.bot.db.add_case(ctx.guild.id, user.id, ctx.author.id, "Kick", reason)
        dm_embed = mod_embed("You Have Been Kicked", f"You were kicked from **{ctx.guild.name}**.", gif_key="kick")
        dm_embed.add_field(name="Reason", value=reason)
        await self._dm(user, dm_embed)
        await ctx.guild.kick(user, reason=reason)
        embed = mod_embed("Kick Executed", f"**{user}** has been kicked.", gif_key="kick")
        embed.add_field(name="User",      value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention,              inline=True)
        embed.add_field(name="Reason",    value=reason,                          inline=False)
        await ctx.send(embed=embed)
        await log_action(self.bot, ctx.guild, "Kick", user, ctx.author, reason)

    # ── MUTE ──────────────────────────────────────────────────────────────────
    @commands.command(name="mute")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def mute(self, ctx, user: discord.Member = None, duration: str = "10m", *, reason: str = "No reason provided"):
        privileged = await _is_privileged(ctx)
        if not privileged:
            return await ctx.send(embed=error_embed(
                "Access Denied",
                "You do not have permission to use this command.",
                gif_key="error"
            ))
        if user is None:
            return await ctx.send(embed=_usage_embed(
                "Missing User",
                "Usage: `!mute <user> [duration] [reason]`\nDuration examples: `10s`, `5m`, `2h`, `1d`"
            ))
        if user.id in (ctx.author.id, ctx.guild.owner.id):
            return await ctx.send(embed=_usage_embed("Permission Denied", "You cannot mute this user."))
        try:
            await hierarchy_check(ctx, user)
        except commands.CheckFailure:
            return
        secs = parse_duration(duration)
        if secs is None:
            return await ctx.send(embed=_usage_embed("Invalid Duration", "Valid formats: `10s`, `5m`, `2h`, `1d`\nMaximum is 28 days."))
        if secs > 2_419_200:
            return await ctx.send(embed=_usage_embed("Duration Too Long", "Maximum timeout duration is **28 days**."))
        await user.edit(timed_out_until=discord.utils.utcnow() + datetime.timedelta(seconds=secs))
        await self.bot.db.add_case(ctx.guild.id, user.id, ctx.author.id, "Mute", reason)
        dm_embed = mod_embed("You Have Been Muted", f"You were muted in **{ctx.guild.name}**.", gif_key="mute")
        dm_embed.add_field(name="Duration", value=duration)
        dm_embed.add_field(name="Reason",   value=reason)
        await self._dm(user, dm_embed)
        embed = mod_embed("Mute Executed", f"**{user}** has been timed out.", gif_key="mute")
        embed.add_field(name="User",      value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="Duration",  value=duration,                        inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention,              inline=True)
        embed.add_field(name="Reason",    value=reason,                          inline=False)
        await ctx.send(embed=embed)
        await log_action(self.bot, ctx.guild, "Mute", user, ctx.author, reason)

    # ── UNMUTE ────────────────────────────────────────────────────────────────
    @commands.command(name="unmute")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def unmute(self, ctx, user: discord.Member = None, *, reason: str = "No reason provided"):
        privileged = await _is_privileged(ctx)
        if not privileged:
            return await ctx.send(embed=error_embed(
                "Access Denied",
                "You do not have permission to use this command.",
                gif_key="error"
            ))
        if user is None:
            return await ctx.send(embed=_usage_embed(
                "Missing User",
                "Usage: `!unmute <user> [reason]`"
            ))
        await user.edit(timed_out_until=None)
        await self.bot.db.add_case(ctx.guild.id, user.id, ctx.author.id, "Unmute", reason)
        embed = mod_embed("Unmute Executed", f"**{user}** has been unmuted.", gif_key="unmute")
        embed.add_field(name="User",      value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention,              inline=True)
        embed.add_field(name="Reason",    value=reason,                          inline=False)
        await ctx.send(embed=embed)
        await log_action(self.bot, ctx.guild, "Unmute", user, ctx.author, reason)

    # ── WARN ──────────────────────────────────────────────────────────────────
    @commands.command(name="warn")
    @commands.cooldown(2, 10, commands.BucketType.user)
    async def warn(self, ctx, user: discord.Member = None, *, reason: str = "No reason provided"):
        privileged = await _is_privileged(ctx)
        if not privileged:
            # Show a generic error for non-privileged users
            return await ctx.send(embed=error_embed(
                "Access Denied",
                "You do not have permission to use this command.",
                gif_key="error"
            ))
        if user is None:
            # Show a usage error for privileged users
            return await ctx.send(embed=_usage_embed(
                "Missing User",
                "Usage: `!warn <user> [reason]`"
            ))
        await self.bot.db.add_case(ctx.guild.id, user.id, ctx.author.id, "Warn", reason)
        warns = await self.bot.db.get_warnings(ctx.guild.id, user.id)
        dm_embed = mod_embed("You Have Been Warned", f"You received a warning in **{ctx.guild.name}**.", gif_key="warn")
        dm_embed.add_field(name="Reason",          value=reason)
        dm_embed.add_field(name="Total Warnings",  value=str(len(warns)))
        await self._dm(user, dm_embed)
        embed = mod_embed("Warning Issued", f"**{user}** has been warned.", gif_key="warn")
        embed.add_field(name="User",           value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="Total Warnings", value=str(len(warns)),                 inline=True)
        embed.add_field(name="Moderator",      value=ctx.author.mention,              inline=True)
        embed.add_field(name="Reason",         value=reason,                          inline=False)
        await ctx.send(embed=embed)
        await log_action(self.bot, ctx.guild, "Warn", user, ctx.author, reason)
        # Auto-mute at 3 warnings
        if len(warns) >= 3:
            try:
                await user.edit(
                    timed_out_until=discord.utils.utcnow() + datetime.timedelta(minutes=10),
                    reason="Auto-mute: reached 3 warnings"
                )
                await self.bot.db.add_case(ctx.guild.id, user.id, ctx.guild.me.id, "Mute", "Auto-mute: reached 3 warnings")
                auto_embed = mod_embed(
                    "Auto-Mute Applied",
                    f"{user.mention} has been automatically muted for **10 minutes** for reaching **3 warnings**.",
                    gif_key="mute"
                )
                await ctx.send(embed=auto_embed)
                try:
                    dm = mod_embed("You Have Been Auto-Muted", f"You were muted in **{ctx.guild.name}** for reaching 3 warnings.", gif_key="mute")
                    dm.add_field(name="Duration", value="10 minutes")
                    await user.send(embed=dm)
                except (discord.Forbidden, discord.HTTPException):
                    pass
                await log_action(self.bot, ctx.guild, "Mute", user, ctx.guild.me, "Auto-mute: reached 3 warnings")
            except discord.Forbidden:
                await ctx.send(embed=_usage_embed("Auto-Mute Failed", f"I don't have permission to mute {user.mention}."))

    # ── WARNINGS ──────────────────────────────────────────────────────────────
    @commands.command(name="warnings")
    async def warnings(self, ctx, user: discord.Member = None):
        if not await _is_privileged(ctx):
            return await _deny_and_alert(ctx, "warnings")
        if not user:
            return await ctx.send(embed=_usage_embed("Missing User", "Usage: `!warnings <user>`"))
        warns = await self.bot.db.get_warnings(ctx.guild.id, user.id)
        if not warns:
            return await ctx.send(embed=success_embed("No Warnings", f"{user.mention} has a clean record."))
        embed = mod_embed(f"Warnings — {user.display_name}", gif_key="warnings")
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="User", value=f"{user.mention} (`{user.id}`)", inline=False)
        for case_id, mod_id, reason, ts in warns[:10]:
            mod = ctx.guild.get_member(mod_id)
            embed.add_field(
                name=f"Warning #{case_id}",
                value=f"**Reason:** {reason[:100]}\n**Mod:** {mod.mention if mod else f'`{mod_id}`'}\n**When:** {ts}",
                inline=False
            )
        embed.set_footer(text=f"{len(warns)} total warning(s)")
        await ctx.send(embed=embed)

    # ── DELWARN ───────────────────────────────────────────────────────────────
    @commands.command(name="delwarn")
    async def delwarn(self, ctx, user: discord.Member = None):
        if not await _is_privileged(ctx):
            return await _deny_and_alert(ctx, "delwarn")
        if not user:
            return await ctx.send(embed=_usage_embed("Missing User", "Usage: `!delwarn <user>`"))
        warns = await self.bot.db.get_warnings(ctx.guild.id, user.id)
        if not warns:
            return await ctx.send(embed=_usage_embed("No Warnings", f"{user.mention} has no warnings to delete."))
        view = DelWarnView(self.bot, ctx.guild, user, warns[:25])
        embed = mod_embed(
            f"Delete Warning — {user.display_name}",
            f"Select a warning to delete from the dropdown.\n{user.mention} has **{len(warns)}** warning(s)."
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        await ctx.send(embed=embed, view=view)

    # ── MODLOGS ───────────────────────────────────────────────────────────────
    @commands.command(name="modlogs", aliases=["history", "cases"])
    async def modlogs(self, ctx, user: discord.Member = None):
        if not await _is_privileged(ctx):
            return await _deny_and_alert(ctx, "modlogs")
        if not user:
            return await ctx.send(embed=_usage_embed("Missing User", "Usage: `!modlogs <user>`"))
        cases = await self.bot.db.get_cases(ctx.guild.id, user.id)
        if not cases:
            return await ctx.send(embed=success_embed("No Cases", f"{user.mention} has no moderation history."))
        embed = success_embed(f"Mod History — {user.display_name}")
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(
            name="User",
            value=f"{user.mention} (`{user.id}`)\n"
                  f"Joined: <t:{int(user.joined_at.timestamp())}:R>\n"
                  f"Created: <t:{int(user.created_at.timestamp())}:R>",
            inline=False
        )
        embed.add_field(name="\u200b", value="**Moderation History**", inline=False)
        for _, action, mod_id, reason, ts in cases[:10]:
            mod = ctx.guild.get_member(mod_id)
            embed.add_field(
                name=f"{action} — {reason[:80]}",
                value=f"**Mod:** {mod.mention if mod else f'`{mod_id}`'}\n**When:** {ts}",
                inline=False
            )
        embed.set_footer(text=f"{len(cases)} total case(s)")
        await ctx.send(embed=embed)

    # ── MODACTIONS ────────────────────────────────────────────────────────────
    @commands.command(name="modactions")
    async def modactions(self, ctx, user: discord.Member = None):
        if not await _is_privileged(ctx):
            return await _deny_and_alert(ctx, "modactions")
        if not user:
            return await ctx.send(embed=_usage_embed("Missing User", "Usage: `!modactions <user>`"))
        cases = await self.bot.db.get_actions_by_mod(ctx.guild.id, user.id)
        if not cases:
            return await ctx.send(embed=success_embed("No Actions", f"{user.mention} has not taken any moderation actions."))
        embed = success_embed(f"Mod Actions By — {user.display_name}")
        embed.set_thumbnail(url=user.display_avatar.url)
        for _, action, target_id, reason, ts in cases[:10]:
            target = ctx.guild.get_member(target_id)
            embed.add_field(
                name=f"{action} on {target.mention if target else f'`{target_id}`'}",
                value=f"**Reason:** {reason[:80]}\n**When:** {ts}",
                inline=False
            )
        embed.set_footer(text=f"{len(cases)} total action(s)")
        await ctx.send(embed=embed)

    # ── PURGE ─────────────────────────────────────────────────────────────────
    @commands.command(name="purge")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def purge(self, ctx, amount: int = None):
        if not await _is_privileged(ctx):
            return await _deny_and_alert(ctx, "purge")
        if not amount:
            return await ctx.send(embed=_usage_embed("Missing Amount", "Usage: `!purge <1-500>`"))
        if not 1 <= amount <= 500:
            return await ctx.send(embed=_usage_embed("Invalid Amount", "Amount must be between **1** and **500**."))
        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(embed=mod_embed("Purge Complete", f"Deleted **{len(deleted)}** messages.", gif_key="purge"), delete_after=5)
        await log_action(self.bot, ctx.guild, "Purge", None, ctx.author, f"Purged {len(deleted)} msgs in #{ctx.channel.name}")

    # ── PURGEUSER ─────────────────────────────────────────────────────────────
    @commands.command(name="ban")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def ban(self, ctx, user: discord.Member = None, *, reason: str = "No reason provided"):
        # Permission check FIRST — before anything else
        if not await _is_privileged(ctx):
            return await _deny_and_alert(ctx, "ban")
        # Only privileged users see argument errors
        if user is None:
            return  # Do not show missing argument error to non-privileged users
        if user.id in (ctx.author.id, ctx.guild.owner.id):
            return await ctx.send(embed=_usage_embed("Permission Denied", "You cannot ban this user."))
        try:
            await hierarchy_check(ctx, user)
        except commands.CheckFailure:
            return
        await self.bot.db.add_case(ctx.guild.id, user.id, ctx.author.id, "Ban", reason)
        dm_embed = mod_embed("You Have Been Banned", f"You were banned from **{ctx.guild.name}**.", gif_key="ban")
        dm_embed.add_field(name="Reason", value=reason)
        await self._dm(user, dm_embed)
        await ctx.guild.ban(user, reason=reason)
        embed = mod_embed("Ban Executed", f"**{user}** has been banned.", gif_key="ban")
        embed.add_field(name="User",      value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention,              inline=True)
        embed.add_field(name="Reason",    value=reason,                          inline=False)
        await ctx.send(embed=embed)
        await log_action(self.bot, ctx.guild, "Ban", user, ctx.author, reason)
        await log_action(self.bot, ctx.guild, "Lock", None, ctx.author, f"#{channel.name}: {reason}")

    # ── UNLOCK ────────────────────────────────────────────────────────────────
    @commands.command(name="unlock")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def unlock(self, ctx, channel: discord.TextChannel = None, *, reason: str = "No reason provided"):
        if not await _is_privileged(ctx):
            return await _deny_and_alert(ctx, "unlock")
        channel = channel or ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=True)
        embed = mod_embed("Channel Unlocked", f"{channel.mention} has been unlocked.\n**Reason:** {reason}", gif_key="unlock")
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)
        await log_action(self.bot, ctx.guild, "Unlock", None, ctx.author, f"#{channel.name}: {reason}")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
