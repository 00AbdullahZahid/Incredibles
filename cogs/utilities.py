import discord
from discord.ext import commands
from core.utils import success_embed, warn_embed, error_embed, mod_embed, PURPLE, BLACK, _get_gif
import logging
import time

log = logging.getLogger("cogs.utilities")

LOG_SETTERS = {
    "general":  ("set_log_channel",      "General Log"),
    "mute":     ("set_log_mute",         "Mute/Unmute/Warn Log"),
    "ban":      ("set_log_ban",          "Ban/Unban/Kick Log"),
    "role":     ("set_log_role",         "Role Log"),
    "music":    ("set_log_music",        "Music Log"),
    "voice":    ("set_log_voice",        "Voice Log"),
    "ticket":   ("set_log_ticket",       "Ticket Log"),
    "member":   ("set_log_member",       "Member Join/Leave Log"),
    "message":  ("set_log_message",      "Message Edit/Delete Log"),
    "server":   ("set_log_server",       "Server Update Log"),
    "channel":  ("set_log_channel_log",  "Channel Create/Delete Log"),
}

# Channel name → (db setter, display label)
LOG_CHANNELS = [
    ("mod-logs",     "set_log_ban",         "Ban / Kick / Unban"),
    ("mute-logs",    "set_log_mute",        "Mute / Unmute / Warn"),
    ("member-logs",  "set_log_member",      "Member Join / Leave"),
    ("message-logs", "set_log_message",     "Message Edit / Delete"),
    ("voice-logs",   "set_log_voice",       "Voice Channel Actions"),
    ("role-logs",    "set_log_role",        "Role Changes"),
    ("music-logs",   "set_log_music",       "Music Playback"),
    ("ticket-logs",  "set_log_ticket",      "Tickets"),
    ("server-logs",  "set_log_server",      "Server Updates"),
    ("channel-logs", "set_log_channel_log", "Channel Create/Delete"),
]


class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── PING ──────────────────────────────────────────────────────────────────
    @commands.command(name="ping")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ping(self, ctx):
        api_ms = round(self.bot.latency * 1000)

        # Measure DB ping
        db_start = time.perf_counter()
        await self.bot.db.get_log_channel(ctx.guild.id)
        db_ms = round((time.perf_counter() - db_start) * 1000)

        # Measure response (round-trip) time
        rtt_start = time.perf_counter()
        tmp = await ctx.send("...")
        rtt_ms = round((time.perf_counter() - rtt_start) * 1000)
        await tmp.delete()

        if api_ms < 100:
            speed_label = "Very Fast"
            color = discord.Color.green()
        elif api_ms < 200:
            speed_label = "Fast"
            color = PURPLE
        elif api_ms < 350:
            speed_label = "Average"
            color = discord.Color.yellow()
        else:
            speed_label = "Slow"
            color = discord.Color.red()

        embed = discord.Embed(color=color)
        embed.add_field(name="Bot Ping",      value=f"**{api_ms}ms**",  inline=False)
        embed.add_field(name="Database Ping", value=f"**{db_ms}ms**",   inline=False)
        embed.add_field(name="Response Time", value=f"**{rtt_ms}ms**",  inline=False)
        embed.add_field(name="Speed",         value=f"**{speed_label}**", inline=False)
        gif = _get_gif("ping")
        if gif:
            embed.set_image(url=gif)
        await ctx.send(embed=embed)

    # ── SERVER INFO ───────────────────────────────────────────────────────────
    @commands.command(name="serverinfo", aliases=["si"])
    async def serverinfo(self, ctx):
        g = ctx.guild
        bots = sum(1 for m in g.members if m.bot)
        humans = g.member_count - bots

        embed = discord.Embed(title=g.name, color=PURPLE)
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)

        embed.add_field(
            name="About",
            value=(
                f"**ID:** `{g.id}`\n"
                f"**Owner:** {g.owner.mention if g.owner else 'Unknown'}\n"
                f"**Created:** <t:{int(g.created_at.timestamp())}:R>\n"
                f"**Verification:** {str(g.verification_level).title()}"
            ),
            inline=False
        )
        embed.add_field(
            name="Members",
            value=f"**Total:** {g.member_count}\n**Humans:** {humans}\n**Bots:** {bots}",
            inline=True
        )
        embed.add_field(
            name="Channels",
            value=f"**Text:** {len(g.text_channels)}\n**Voice:** {len(g.voice_channels)}\n**Categories:** {len(g.categories)}",
            inline=True
        )
        embed.add_field(
            name="Boosts",
            value=f"**Level:** {g.premium_tier}\n**Boosts:** {g.premium_subscription_count}",
            inline=True
        )
        embed.add_field(name="Roles",  value=str(len(g.roles)),  inline=True)
        embed.add_field(name="Emojis", value=str(len(g.emojis)), inline=True)
        features = ", ".join(f.replace("_", " ").title() for f in g.features) or "None"
        embed.add_field(name="Features", value=features, inline=False)
        gif = _get_gif("serverinfo")
        if gif:
            embed.set_image(url=gif)
        await ctx.send(embed=embed)

    # ── USER INFO ─────────────────────────────────────────────────────────────
    @commands.command(name="userinfo", aliases=["ui"])
    async def userinfo(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        roles = [r.mention for r in reversed(user.roles) if r != ctx.guild.default_role]
        role_chunks = [roles[i:i+4] for i in range(0, len(roles), 4)]
        role_str = "\n".join(" ".join(chunk) for chunk in role_chunks) if roles else "None"

        badges = []
        if user.bot:                badges.append("Bot")
        if user == ctx.guild.owner: badges.append("Server Owner")
        if user.guild_permissions.administrator: badges.append("Admin")
        if user.premium_since:      badges.append(f"Boosting since <t:{int(user.premium_since.timestamp())}:R>")

        # Key permissions
        p = user.guild_permissions
        key_perms = []
        if p.administrator:       key_perms.append("Administrator")
        if p.manage_guild:        key_perms.append("Manage Server")
        if p.manage_roles:        key_perms.append("Manage Roles")
        if p.manage_channels:     key_perms.append("Manage Channels")
        if p.manage_messages:     key_perms.append("Manage Messages")
        if p.manage_webhooks:     key_perms.append("Manage Webhooks")
        if p.manage_nicknames:    key_perms.append("Manage Nicknames")
        if p.manage_emojis:       key_perms.append("Manage Emojis and Stickers")
        if p.kick_members:        key_perms.append("Kick Members")
        if p.ban_members:         key_perms.append("Ban Members")
        if p.mention_everyone:    key_perms.append("Mention Everyone")
        if p.moderate_members:    key_perms.append("Timeout Members")
        if p.view_audit_log:      key_perms.append("View Audit Log")
        if p.move_members:        key_perms.append("Move Members")
        perms_str = ", ".join(key_perms) if key_perms else "No key permissions"

        embed = discord.Embed(title=user.display_name, color=PURPLE)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(
            name="Information",
            value=(
                f"**Username:** `{user}`\n"
                f"**ID:** `{user.id}`\n"
                f"**Badges:** {', '.join(badges) if badges else 'None'}"
            ),
            inline=False
        )
        embed.add_field(
            name="Dates",
            value=(
                f"**Joined Server:** <t:{int(user.joined_at.timestamp())}:R>\n"
                f"**Account Created:** <t:{int(user.created_at.timestamp())}:R>"
            ),
            inline=False
        )
        embed.add_field(name="Top Role", value=user.top_role.mention, inline=True)
        embed.add_field(name="Color",    value=str(user.color),        inline=True)
        embed.add_field(
            name=f"Roles ({len(roles)})",
            value=role_str[:1024] if role_str else "None",
            inline=False
        )
        embed.add_field(
            name="Key Permissions",
            value=perms_str[:1024],
            inline=False
        )
        embed.set_footer(text="Acknowledgements: " + ("Server Admin" if p.administrator else "Member"))
        gif = _get_gif("userinfo")
        if gif:
            embed.set_image(url=gif)
        await ctx.send(embed=embed)

    # ── AVATAR ────────────────────────────────────────────────────────────────
    @commands.command(name="avatar", aliases=["av"])
    async def avatar(self, ctx, *, user_input: str = None):
        user = None
        if user_input is None:
            user = await self.bot.fetch_user(ctx.author.id)
        else:
            try:
                member = await commands.MemberConverter().convert(ctx, user_input)
                user = await self.bot.fetch_user(member.id)
            except commands.MemberNotFound:
                try:
                    user = await self.bot.fetch_user(int(user_input.strip()))
                except (ValueError, discord.NotFound):
                    return await ctx.send(embed=error_embed("User Not Found", "Provide a mention, username, or valid user ID."))
        embed = success_embed(f"{user.display_name}'s Avatar")
        embed.set_image(url=user.display_avatar.url)
        await ctx.send(embed=embed)

    # ── MEMBER COUNT ──────────────────────────────────────────────────────────
    @commands.command(name="mc", aliases=["membercount", "members"])
    async def mc(self, ctx):
        g = ctx.guild
        total    = g.member_count
        bots     = sum(1 for m in g.members if m.bot)
        humans   = total - bots
        online   = sum(1 for m in g.members if m.status != discord.Status.offline and not m.bot)
        offline  = humans - online
        boosters = g.premium_subscription_count

        embed = discord.Embed(title=f"{g.name} — Member Count", color=PURPLE)
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)
        embed.add_field(name="Total",    value=f"**{total}**",   inline=True)
        embed.add_field(name="Humans",   value=f"**{humans}**",  inline=True)
        embed.add_field(name="Bots",     value=f"**{bots}**",    inline=True)
        embed.add_field(name="Online",   value=f"**{online}**",  inline=True)
        embed.add_field(name="Offline",  value=f"**{offline}**", inline=True)
        embed.add_field(name="Boosters", value=f"**{boosters}**",inline=True)
        embed.set_footer(text=f"Server ID: {g.id}")
        await ctx.send(embed=embed)

    # ── SERVER OWNER ──────────────────────────────────────────────────────────
    @commands.command(name="so", aliases=["serverowner", "owner"])
    async def so(self, ctx):
        g = ctx.guild
        owner = g.owner
        if not owner:
            return await ctx.send(embed=error_embed("Owner Not Found", "Could not find the server owner."))

        embed = discord.Embed(title="Server Owner", color=PURPLE)
        embed.set_thumbnail(url=owner.display_avatar.url)
        embed.add_field(
            name="Owner",
            value=f"{owner.mention}\n`{owner}` (`{owner.id}`)",
            inline=False
        )
        embed.add_field(
            name="Account Created",
            value=f"<t:{int(owner.created_at.timestamp())}:R>",
            inline=True
        )
        embed.add_field(
            name="Joined Server",
            value=f"<t:{int(owner.joined_at.timestamp())}:R>" if owner.joined_at else "Unknown",
            inline=True
        )

        # Show 2nd account if set
        second_id = await self.bot.db.get_owner_second_acc(g.id)
        if second_id:
            second = g.get_member(second_id) or await self.bot.fetch_user(second_id)
            embed.add_field(
                name="Second Account",
                value=f"{second.mention} (`{second.id}`)" if second else f"`{second_id}`",
                inline=False
            )

        # Only owner can set/remove 2nd account
        if ctx.author == owner or ctx.author.id in self.bot.owner_ids:
            embed.set_footer(text="Use !so set @user to set a second account | !so remove to clear it")

        await ctx.send(embed=embed)

    @commands.command(name="soset", aliases=["so set"])
    async def soset(self, ctx, user: discord.Member = None):
        """Set the owner's second account. Owner only."""
        if ctx.author != ctx.guild.owner and ctx.author.id not in self.bot.owner_ids:
            return await ctx.send(embed=error_embed("Access Denied", "Only the server owner can use this command."))
        if not user:
            return await ctx.send(embed=error_embed("Missing User", "Usage: `!soset @user`"))
        await self.bot.db.set_owner_second_acc(ctx.guild.id, user.id)
        embed = success_embed("Second Account Set", f"{user.mention} has been set as the owner's second account.")
        await ctx.send(embed=embed)

    @commands.command(name="soremove")
    async def soremove(self, ctx):
        """Remove the owner's second account. Owner only."""
        if ctx.author != ctx.guild.owner and ctx.author.id not in self.bot.owner_ids:
            return await ctx.send(embed=error_embed("Access Denied", "Only the server owner can use this command."))
        await self.bot.db.set_owner_second_acc(ctx.guild.id, None)
        embed = success_embed("Second Account Removed", "The owner's second account has been cleared.")
        await ctx.send(embed=embed)

    # ── BANNER ────────────────────────────────────────────────────────────────
    @commands.command(name="banner")
    async def banner(self, ctx, *, user_input: str = None):
        user = None
        if user_input is None:
            user = await self.bot.fetch_user(ctx.author.id)
        else:
            try:
                member = await commands.MemberConverter().convert(ctx, user_input)
                user = await self.bot.fetch_user(member.id)
            except commands.MemberNotFound:
                try:
                    user = await self.bot.fetch_user(int(user_input.strip()))
                except (ValueError, discord.NotFound):
                    return await ctx.send(embed=error_embed("User Not Found", "Could not find that user."))
        if not user.banner:
            return await ctx.send(embed=error_embed("No Banner", f"**{user.display_name}** does not have a banner."))
        embed = success_embed(f"{user.display_name}'s Banner")
        embed.set_image(url=user.banner.url)
        await ctx.send(embed=embed)

    # ── AUTOLOGS ──────────────────────────────────────────────────────────────
    @commands.command(name="autologs")
    @commands.has_permissions(administrator=True)
    async def autologs(self, ctx, log_type: str = None, channel: discord.TextChannel = None):
        """Auto-creates the Incredibles Bot Logs category with all channels, OR sets a specific one.
        Run with no args to auto-create everything. Run with a type to set a specific channel."""
        if not ctx.guild.owner == ctx.author and ctx.author.id not in self.bot.owner_ids:
            return await ctx.send(embed=error_embed("Access Denied", "Only the server owner can use this command."))

        # No args — auto-create full log category
        if log_type is None:
            msg = await ctx.send(embed=discord.Embed(
                title="Setting Up Log Channels",
                description="Creating **Incredibles Bot Logs** category and all log channels...",
                color=PURPLE
            ))

            # Build overwrites — admins + bot only
            admin_roles = [r for r in ctx.guild.roles if r.permissions.administrator and r != ctx.guild.default_role]
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True)
            }
            for role in admin_roles:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=False)

            # Create or find category
            category = discord.utils.get(ctx.guild.categories, name="Incredibles Bot Logs")
            if not category:
                category = await ctx.guild.create_category("Incredibles Bot Logs", overwrites=overwrites)
            else:
                await category.edit(overwrites=overwrites)

            created = []
            for ch_name, setter, label in LOG_CHANNELS:
                existing = discord.utils.get(ctx.guild.text_channels, name=ch_name)
                if not existing:
                    ch = await ctx.guild.create_text_channel(ch_name, category=category, overwrites=overwrites)
                else:
                    ch = existing
                    await ch.edit(category=category, overwrites=overwrites)
                created.append((ch, label))
                if hasattr(self.bot.db, setter):
                    await getattr(self.bot.db, setter)(ctx.guild.id, ch.id)

            lines = "\n".join(f"{ch.mention} — {label}" for ch, label in created)
            await msg.edit(embed=discord.Embed(
                title="Log Channels Ready",
                description=f"All log channels have been set up under **Incredibles Bot Logs**:\n\n{lines}",
                color=PURPLE
            ))
            return

        # Specific type — view current or set
        log_type = log_type.lower()

        if log_type == "view":
            embed = discord.Embed(title="Log Channels", color=BLACK)
            getters = {
                "Ban/Kick":     "get_log_ban",
                "Mute/Warn":    "get_log_mute",
                "Role":         "get_log_role",
                "Music":        "get_log_music",
                "Voice":        "get_log_voice",
                "Ticket":       "get_log_ticket",
                "Member":       "get_log_member",
                "Message":      "get_log_message",
                "Server":       "get_log_server",
                "Channel":      "get_log_channel_log",
                "General":      "get_log_channel",
            }
            for label, getter in getters.items():
                cid = await getattr(self.bot.db, getter)(ctx.guild.id)
                ch = ctx.guild.get_channel(cid) if cid else None
                embed.add_field(name=label, value=ch.mention if ch else "Not set", inline=True)
            return await ctx.send(embed=embed)

        if log_type not in LOG_SETTERS:
            types = ", ".join(f"`{k}`" for k in list(LOG_SETTERS.keys()) + ["view"])
            return await ctx.send(embed=error_embed("Invalid Type", f"Valid types:\n{types}\n\nRun `!autologs` with no arguments to auto-create everything."))

        channel = channel or ctx.channel
        setter, label = LOG_SETTERS[log_type]
        await getattr(self.bot.db, setter)(ctx.guild.id, channel.id)
        embed = success_embed("Log Channel Set", f"**{label}** will now log to {channel.mention}.")
        await ctx.send(embed=embed)

    # ── SETALLOWROLES ─────────────────────────────────────────────────────────
    @commands.command(name="setallowroles")
    @commands.has_permissions(administrator=True)
    async def setallowroles(self, ctx, *roles: discord.Role):
        if not ctx.guild.owner == ctx.author and ctx.author.id not in self.bot.owner_ids:
            return await ctx.send(embed=error_embed("Access Denied", "Only the server owner can use this command."))
        role_ids = [r.id for r in roles]
        await self.bot.db.set_allowed_roles(ctx.guild.id, role_ids)
        embed = success_embed("Allowed Roles Updated")
        embed.add_field(
            name="Roles with elevated permissions",
            value=" ".join(r.mention for r in roles) if roles else "None (everyone)",
            inline=False
        )
        embed.set_footer(text="These roles can use privileged commands: ban, kick, mute, lock, purge, etc.")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Utilities(bot))
