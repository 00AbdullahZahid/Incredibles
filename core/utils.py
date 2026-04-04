import discord
from discord.ext import commands
import logging
from datetime import datetime, timezone

log = logging.getLogger("core.utils")

PURPLE = discord.Color(0x9B59B6)   # normal embeds
PINK   = discord.Color(0xCC8899)   # moderation action embeds
YELLOW = discord.Color(0xF1C40F)   # errors / failed commands
BLACK  = discord.Color(0x010101)   # log channel embeds

GIFS = {
    "ban":        "https://cdn.discordapp.com/attachments/1474488131184103678/1474488310650114350/FSp99CD.gif",
    "unban":      "https://cdn.discordapp.com/attachments/1474488131184103678/1474488356388999415/BePRUiE.gif",
    "mute":       "https://cdn.discordapp.com/attachments/1474488131184103678/1474493405156479078/SsdPQQZ.gif",
    "unmute":     "https://cdn.discordapp.com/attachments/1474488131184103678/1474494147716059348/8EfPFhA.gif",
    "kick":       "https://cdn.discordapp.com/attachments/1474488131184103678/1474497645388103902/owHCvFZ.gif",
    "warn":       "https://cdn.discordapp.com/attachments/1474488131184103678/1474498432126292022/Kg6JsoO.gif",
    "warnings":   "https://cdn.discordapp.com/attachments/1474488131184103678/1474498878404559090/wCNYjaD.gif",
    "delwarn":    "https://cdn.discordapp.com/attachments/1474488131184103678/1474501341438021683/GQVAgOW.gif",
    "purge":      "https://cdn.discordapp.com/attachments/1474488131184103678/1474502060497174538/nFmT5v7.gif",
    "purgeuser":  "https://cdn.discordapp.com/attachments/1474488131184103678/1474502060497174538/nFmT5v7.gif",
    "lock":       "https://cdn.discordapp.com/attachments/1474488131184103678/1474503277273157825/JeE2Gdu.gif",
    "unlock":     "https://cdn.discordapp.com/attachments/1474488131184103678/1474504152376807618/h6viBaR.gif",
    "afk":        "https://cdn.discordapp.com/attachments/1474488131184103678/1474506782226383103/TaS660m.gif",
    "afkremove":  "https://cdn.discordapp.com/attachments/1474488131184103678/1474507589948805343/bz7tB0O.gif",
    "help":       "https://cdn.discordapp.com/attachments/1474488131184103678/1474508545839071282/sqOMVqh.gif",
    "ping":       "https://cdn.discordapp.com/attachments/1474488131184103678/1474510239217877246/tTtm6Fq.gif",
    "serverinfo": "https://cdn.discordapp.com/attachments/1474488131184103678/1474512182329872455/5xRCrnu.gif",
    "userinfo":   "https://cdn.discordapp.com/attachments/1474488131184103678/1474511675079000144/n9e3Hm4.gif",
    "music":      "https://cdn.discordapp.com/attachments/1311595689041723475/1464056665514184841/standard_1.gif",
    "error":      "https://cdn.discordapp.com/attachments/1474488131184103678/1474506174677385479/incredibles_warn.gif",
}

LOG_CHANNEL_MAP = {
    "Ban":          "get_log_ban",
    "Unban":        "get_log_ban",
    "Kick":         "get_log_ban",
    "Mute":         "get_log_mute",
    "Unmute":       "get_log_mute",
    "Warn":         "get_log_mute",
    "Purge":        "get_log_ban",
    "Lock":         "get_log_ban",
    "Unlock":       "get_log_ban",
    "Role Added":   "get_log_role",
    "Role Removed": "get_log_role",
    "VCBan":        "get_log_voice",
    "VCUnban":      "get_log_voice",
    "VCKick":       "get_log_voice",
    "VCMoveAll":    "get_log_voice",
    "AddUser":      "get_log_voice",
    "Ticket":       "get_log_ticket",
    "Music":        "get_log_music",
}

ACTION_CHANNEL_NAME = {
    "Ban":          "mod-logs",
    "Unban":        "mod-logs",
    "Kick":         "mod-logs",
    "Mute":         "mod-logs",
    "Unmute":       "mod-logs",
    "Warn":         "mod-logs",
    "Purge":        "mod-logs",
    "Lock":         "mod-logs",
    "Unlock":       "mod-logs",
    "Role Added":   "role-logs",
    "Role Removed": "role-logs",
    "VCBan":        "voice-logs",
    "VCUnban":      "voice-logs",
    "VCKick":       "voice-logs",
    "VCMoveAll":    "voice-logs",
    "AddUser":      "voice-logs",
    "Ticket":       "mod-logs",
    "Music":        "mod-logs",
}


def _get_gif(key: str):
    return GIFS.get(key) or None


def _base_embed(title, description=None, color=None):
    return discord.Embed(title=title, description=description, color=color or PURPLE)


# Purple — general / info embeds
def success_embed(title, description=None, guild=None, gif_key=None):
    embed = _base_embed(title, description, PURPLE)
    if gif_key:
        gif = _get_gif(gif_key)
        if gif:
            embed.set_image(url=gif)
    return embed


# Pink — moderation action embeds (ban, kick, mute, warn, purge, lock, etc.)
def mod_embed(title, description=None, gif_key=None):
    embed = _base_embed(title, description, PINK)
    if gif_key:
        gif = _get_gif(gif_key)
        if gif:
            embed.set_image(url=gif)
    return embed


# Yellow — errors and failed/denied commands (with optional error gif)
def error_embed(title, description=None, gif_key=None):
    embed = _base_embed(title, description, YELLOW)
    if gif_key:
        gif = _get_gif(gif_key)
        if gif:
            embed.set_image(url=gif)
    return embed


def warn_embed(title, description=None, gif_key=None):
    embed = _base_embed(title, description, YELLOW)
    if gif_key:
        gif = _get_gif(gif_key)
        if gif:
            embed.set_image(url=gif)
    return embed


# Black — log channel embeds only
def log_embed_build(title, description=None):
    return _base_embed(title, description, BLACK)


async def hierarchy_check(ctx, target: discord.Member) -> bool:
    if target.top_role >= ctx.guild.me.top_role:
        await ctx.send(embed=error_embed(
            "Role Hierarchy Error",
            f"My highest role is below **{target.top_role.name}**. Move my role higher to action this user."
        ))
        raise commands.CheckFailure()
    if ctx.author != ctx.guild.owner and target.top_role >= ctx.author.top_role:
        await ctx.send(embed=error_embed(
            "Role Hierarchy Error",
            f"**{target.display_name}**'s role is equal to or above yours."
        ))
        raise commands.CheckFailure()
    return True


async def has_allowed_role(ctx) -> bool:
    if ctx.author == ctx.guild.owner or ctx.author.id in ctx.bot.owner_ids:
        return True
    allowed = await ctx.bot.db.get_allowed_roles(ctx.guild.id)
    if not allowed:
        return True
    return any(r.id in allowed for r in ctx.author.roles)



async def log_action(
    bot, guild, action, target=None, moderator=None, reason=None, log_type="mod", extra=None
):
    """
    Generalized logging function for all log types.
    log_type: mod, member, message, purge, role, voice, server, channel, invite, bot, thread, timeout, etc.
    extra: dict of additional fields to add to the embed.
    """
    channel = await _resolve_log_channel(bot, guild, action, log_type)
    if not channel:
        return

    # Color coding by log type
    LOG_COLORS = {
        "mod": 0xE74C3C,      # Red
        "member": 0x3498DB,   # Blue
        "message": 0x95A5A6,  # Gray
        "purge": 0xF1C40F,    # Yellow
        "role": 0x9B59B6,     # Purple
        "voice": 0x1ABC9C,    # Teal
        "server": 0x2ECC71,   # Green
        "channel": 0xE67E22,  # Orange
        "invite": 0x00BFFF,   # DeepSkyBlue
        "bot": 0x636e72,      # Dark Gray
        "thread": 0x00B894,   # Light Green
        "timeout": 0xFFC300,  # Gold
    }
    color = LOG_COLORS.get(log_type, BLACK)

    embed = discord.Embed(
        title=f"{action} Log",
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    if target is not None:
        embed.add_field(
            name="User",
            value=(getattr(target, "mention", str(target)) + f" (`{getattr(target, 'id', 'N/A')}`)"),
            inline=True
        )
        if hasattr(target, "avatar"):
            embed.set_thumbnail(url=target.avatar.url if target.avatar else discord.Embed.Empty)
    if moderator is not None:
        embed.add_field(
            name="Moderator",
            value=(getattr(moderator, "mention", str(moderator)) + f" (`{getattr(moderator, 'id', 'N/A')}`)"),
            inline=True
        )
    if reason is not None:
        embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
    if extra:
        for k, v in extra.items():
            embed.add_field(name=k, value=v, inline=False)
    embed.set_footer(text=f"Log Type: {log_type} | Action: {action}")
    try:
        await channel.send(embed=embed)
    except Exception as e:
        log.error("Log send error: %s", e)


async def _resolve_log_channel(bot, guild, action, log_type="mod"):
    # Try log_type-specific getter first
    log_type_map = {
        "mod": "get_log_ban",
        "member": "get_log_member",
        "message": "get_log_message",
        "purge": "get_log_ban",
        "role": "get_log_role",
        "voice": "get_log_voice",
        "server": "get_log_server",
        "channel": "get_log_channel",
        "invite": "get_log_invite",
        "bot": "get_log_bot",
        "thread": "get_log_thread",
        "timeout": "get_log_mute",
    }
    getter = log_type_map.get(log_type) or LOG_CHANNEL_MAP.get(action)
    if getter and hasattr(bot.db, getter):
        cid = await getattr(bot.db, getter)(guild.id)
        if cid:
            ch = guild.get_channel(cid)
            if ch:
                return ch
    ch_name = ACTION_CHANNEL_NAME.get(action, f"{log_type}-logs")
    ch = discord.utils.get(guild.text_channels, name=ch_name)
    if ch:
        return ch
    cid = await bot.db.get_log_channel(guild.id)
    if cid:
        ch = guild.get_channel(cid)
        if ch:
            return ch
    return None


def parse_duration(duration: str):
    try:
        if duration.endswith("s"):   return int(duration[:-1])
        elif duration.endswith("m"): return int(duration[:-1]) * 60
        elif duration.endswith("h"): return int(duration[:-1]) * 3600
        elif duration.endswith("d"): return int(duration[:-1]) * 86400
    except ValueError:
        pass
    return None
