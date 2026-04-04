import discord
from discord.ext import commands
from core.utils import BLACK
from datetime import datetime, timezone
import logging

log = logging.getLogger("cogs.logging")

DB_MAP = {
    "member-logs":  ("set_log_member",      "get_log_member"),
    "message-logs": ("set_log_message",     "get_log_message"),
    "voice-logs":   ("set_log_voice",       "get_log_voice"),
    "server-logs":  ("set_log_server",      "get_log_server"),
    "channel-logs": ("set_log_channel_log", "get_log_channel_log"),
    "role-logs":    ("set_log_role",        "get_log_role"),
    "mod-logs":     ("set_log_ban",         "get_log_ban"),
    "music-logs":   ("set_log_music",       "get_log_music"),
}


async def _get_log_channel(bot, guild, channel_name: str):
    getter = DB_MAP.get(channel_name, (None, None))[1]
    if getter and hasattr(bot.db, getter):
        cid = await getattr(bot.db, getter)(guild.id)
        if cid:
            ch = guild.get_channel(cid)
            if ch:
                return ch
    return None


def _base_log(title: str, color: discord.Color = BLACK) -> discord.Embed:
    return discord.Embed(title=title, color=color, timestamp=datetime.now(timezone.utc))


class LoggingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── 2. MEMBER LOGS ────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        ch = await _get_log_channel(self.bot, member.guild, "member-logs")
        if not ch:
            return
        embed = _base_log("Member Joined", discord.Color.green())
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="User",         value=f"{member.mention}\n`{member.id}`",                  inline=True)
        embed.add_field(name="Account Age",  value=f"<t:{int(member.created_at.timestamp())}:R>",       inline=True)
        embed.add_field(name="Member Count", value=str(member.guild.member_count),                      inline=True)
        embed.set_footer(text=f"ID: {member.id}")
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        ch = await _get_log_channel(self.bot, member.guild, "member-logs")
        if not ch:
            return
        roles = [r.mention for r in reversed(member.roles) if r != member.guild.default_role]
        embed = _base_log("Member Left", discord.Color.red())
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="User",   value=f"{member.mention}\n`{member.id}`",                                       inline=True)
        embed.add_field(name="Joined", value=f"<t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "Unknown", inline=True)
        embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles[:8]) if roles else "None", inline=False)
        embed.set_footer(text=f"ID: {member.id}")
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Nickname change → member-logs
        if before.nick != after.nick:
            ch = await _get_log_channel(self.bot, after.guild, "member-logs")
            if ch:
                embed = _base_log("Nickname Changed", BLACK)
                embed.set_author(name=str(after), icon_url=after.display_avatar.url)
                embed.add_field(name="User",   value=f"{after.mention} (`{after.id}`)", inline=False)
                embed.add_field(name="Before", value=before.nick or before.name,        inline=True)
                embed.add_field(name="After",  value=after.nick  or after.name,         inline=True)
                embed.set_footer(text=f"ID: {after.id}")
                await ch.send(embed=embed)

        # Role changes → role-logs
        added   = [r for r in after.roles  if r not in before.roles]
        removed = [r for r in before.roles if r not in after.roles]
        if added or removed:
            ch = await _get_log_channel(self.bot, after.guild, "role-logs")
            if ch:
                if added:
                    embed = _base_log("Role Added to Member", discord.Color.green())
                    embed.set_author(name=str(after), icon_url=after.display_avatar.url)
                    embed.add_field(name="User",        value=f"{after.mention} (`{after.id}`)",            inline=False)
                    embed.add_field(name="Roles Added", value=", ".join(r.mention for r in added),          inline=False)
                    embed.set_footer(text=f"ID: {after.id}")
                    await ch.send(embed=embed)
                if removed:
                    embed = _base_log("Role Removed from Member", discord.Color.orange())
                    embed.set_author(name=str(after), icon_url=after.display_avatar.url)
                    embed.add_field(name="User",          value=f"{after.mention} (`{after.id}`)",          inline=False)
                    embed.add_field(name="Roles Removed", value=", ".join(r.mention for r in removed),      inline=False)
                    embed.set_footer(text=f"ID: {after.id}")
                    await ch.send(embed=embed)

    # ── 3. MESSAGE LOGS ───────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild:
            return
        if before.content == after.content:
            return
        ch = await _get_log_channel(self.bot, before.guild, "message-logs")
        if not ch:
            return
        embed = _base_log("Message Edited", discord.Color.yellow())
        embed.set_author(name=str(before.author), icon_url=before.author.display_avatar.url)
        embed.add_field(name="Author",          value=f"{before.author.mention} (`{before.author.id}`)", inline=True)
        embed.add_field(name="Channel",         value=before.channel.mention,                            inline=True)
        embed.add_field(name="Before",          value=before.content[:1024] or "Empty",                  inline=False)
        embed.add_field(name="After",           value=after.content[:1024]  or "Empty",                  inline=False)
        embed.add_field(name="Jump to Message", value=f"[Click here]({after.jump_url})",                 inline=False)
        embed.set_footer(text=f"Message ID: {before.id}")
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        ch = await _get_log_channel(self.bot, message.guild, "message-logs")
        if not ch:
            return
        embed = _base_log("Message Deleted", discord.Color.red())
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
        embed.add_field(name="Author",  value=f"{message.author.mention} (`{message.author.id}`)", inline=True)
        embed.add_field(name="Channel", value=message.channel.mention,                             inline=True)
        embed.add_field(name="Content", value=message.content[:1024] or "Empty / Attachment only", inline=False)
        if message.attachments:
            embed.add_field(
                name=f"Attachments ({len(message.attachments)})",
                value="\n".join(a.filename for a in message.attachments),
                inline=False
            )
        embed.set_footer(text=f"Message ID: {message.id}")
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list):
        if not messages or not messages[0].guild:
            return
        ch = await _get_log_channel(self.bot, messages[0].guild, "message-logs")
        if not ch:
            return
        embed = _base_log("Bulk Messages Deleted (Purge)", discord.Color.red())
        embed.add_field(name="Channel",  value=messages[0].channel.mention, inline=True)
        embed.add_field(name="Deleted",  value=f"**{len(messages)}** messages", inline=True)
        embed.set_footer(text="Purge action")
        await ch.send(embed=embed)

    # ── 5. ROLE LOGS ──────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        ch = await _get_log_channel(self.bot, role.guild, "role-logs")
        if not ch:
            return
        embed = _base_log("Role Created", discord.Color.green())
        embed.add_field(name="Role",        value=f"{role.mention} (`{role.id}`)",         inline=True)
        embed.add_field(name="Color",       value=str(role.color),                         inline=True)
        embed.add_field(name="Hoisted",     value="Yes" if role.hoist else "No",           inline=True)
        embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No",     inline=True)
        embed.set_footer(text=f"Role ID: {role.id}")
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        ch = await _get_log_channel(self.bot, role.guild, "role-logs")
        if not ch:
            return
        embed = _base_log("Role Deleted", discord.Color.red())
        embed.add_field(name="Name", value=f"`{role.name}`", inline=True)
        embed.add_field(name="ID",   value=f"`{role.id}`",   inline=True)
        embed.set_footer(text=f"Role ID: {role.id}")
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        ch = await _get_log_channel(self.bot, after.guild, "role-logs")
        if not ch:
            return
        changes = []
        if before.name != after.name:
            changes.append(f"**Name:** `{before.name}` → `{after.name}`")
        if before.color != after.color:
            changes.append(f"**Color:** `{before.color}` → `{after.color}`")
        if before.hoist != after.hoist:
            changes.append(f"**Hoisted:** `{before.hoist}` → `{after.hoist}`")
        if before.mentionable != after.mentionable:
            changes.append(f"**Mentionable:** `{before.mentionable}` → `{after.mentionable}`")
        if not changes:
            return
        embed = _base_log("Role Updated", discord.Color.yellow())
        embed.add_field(name="Role",    value=after.mention,      inline=True)
        embed.add_field(name="Changes", value="\n".join(changes), inline=False)
        embed.set_footer(text=f"Role ID: {after.id}")
        await ch.send(embed=embed)

    # ── 6. VOICE LOGS ─────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        ch = await _get_log_channel(self.bot, member.guild, "voice-logs")
        if not ch:
            return
        if before.channel is None and after.channel is not None:
            embed = _base_log("Joined Voice Channel", discord.Color.green())
            embed.set_author(name=str(member), icon_url=member.display_avatar.url)
            embed.add_field(name="Member",  value=f"{member.mention} (`{member.id}`)", inline=True)
            embed.add_field(name="Channel", value=after.channel.name,                  inline=True)
        elif before.channel is not None and after.channel is None:
            embed = _base_log("Left Voice Channel", discord.Color.red())
            embed.set_author(name=str(member), icon_url=member.display_avatar.url)
            embed.add_field(name="Member",  value=f"{member.mention} (`{member.id}`)", inline=True)
            embed.add_field(name="Channel", value=before.channel.name,                 inline=True)
        elif before.channel and after.channel and before.channel != after.channel:
            embed = _base_log("Switched Voice Channel", discord.Color.yellow())
            embed.set_author(name=str(member), icon_url=member.display_avatar.url)
            embed.add_field(name="Member", value=f"{member.mention} (`{member.id}`)", inline=False)
            embed.add_field(name="From",   value=before.channel.name,                 inline=True)
            embed.add_field(name="To",     value=after.channel.name,                  inline=True)
        else:
            return
        embed.set_footer(text=f"ID: {member.id}")
        await ch.send(embed=embed)

    # ── 7. SERVER LOGS ────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        ch = await _get_log_channel(self.bot, after, "server-logs")
        if not ch:
            return
        changes = []
        if before.name != after.name:
            changes.append(f"**Name:** `{before.name}` → `{after.name}`")
        if before.icon != after.icon:
            changes.append("**Server icon** was updated")
        if before.banner != after.banner:
            changes.append("**Server banner** was updated")
        if before.verification_level != after.verification_level:
            changes.append(f"**Verification Level:** `{before.verification_level}` → `{after.verification_level}`")
        if before.explicit_content_filter != after.explicit_content_filter:
            changes.append(f"**Content Filter:** `{before.explicit_content_filter}` → `{after.explicit_content_filter}`")
        if not changes:
            return
        embed = _base_log("Server Updated", BLACK)
        embed.set_thumbnail(url=after.icon.url if after.icon else None)
        embed.add_field(name="Changes", value="\n".join(changes), inline=False)
        embed.set_footer(text=f"Server ID: {after.id}")
        await ch.send(embed=embed)

    # ── 8. CHANNEL LOGS ───────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        ch = await _get_log_channel(self.bot, channel.guild, "channel-logs")
        if not ch:
            return
        embed = _base_log("Channel Created", discord.Color.green())
        embed.add_field(name="Name",     value=channel.mention if hasattr(channel, 'mention') else f"`{channel.name}`", inline=True)
        embed.add_field(name="Type",     value=str(channel.type).replace("_", " ").title(),                              inline=True)
        embed.add_field(name="Category", value=channel.category.name if channel.category else "None",                    inline=True)
        embed.set_footer(text=f"Channel ID: {channel.id}")
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        ch = await _get_log_channel(self.bot, channel.guild, "channel-logs")
        if not ch:
            return
        embed = _base_log("Channel Deleted", discord.Color.red())
        embed.add_field(name="Name",     value=f"`#{channel.name}`",                                      inline=True)
        embed.add_field(name="Type",     value=str(channel.type).replace("_", " ").title(),               inline=True)
        embed.add_field(name="Category", value=channel.category.name if channel.category else "None",     inline=True)
        embed.set_footer(text=f"Channel ID: {channel.id}")
        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        ch = await _get_log_channel(self.bot, after.guild, "channel-logs")
        if not ch:
            return
        changes = []
        if before.name != after.name:
            changes.append(f"**Name:** `#{before.name}` → `#{after.name}`")
        if hasattr(before, 'topic') and before.topic != after.topic:
            changes.append(f"**Topic:** `{before.topic or 'None'}` → `{after.topic or 'None'}`")
        if hasattr(before, 'slowmode_delay') and before.slowmode_delay != after.slowmode_delay:
            changes.append(f"**Slowmode:** `{before.slowmode_delay}s` → `{after.slowmode_delay}s`")
        if not changes:
            return
        embed = _base_log("Channel Updated", discord.Color.yellow())
        embed.add_field(name="Channel", value=after.mention if hasattr(after, 'mention') else f"`#{after.name}`", inline=True)
        embed.add_field(name="Changes", value="\n".join(changes),                                                  inline=False)
        embed.set_footer(text=f"Channel ID: {after.id}")
        await ch.send(embed=embed)


async def setup(bot):
    await bot.add_cog(LoggingCog(bot))
