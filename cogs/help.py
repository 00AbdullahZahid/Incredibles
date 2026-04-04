import discord
from discord.ext import commands
from core.utils import PURPLE, _get_gif
import logging

log = logging.getLogger("cogs.help")

MODULE_EMOJI_IDS = {
    "Moderation": ("Moderatiion", 1480133095368818860),
    "Music":      ("music",       1480133097306460180),
    "Voice":      ("Voice",       1480133118265528454),
    "AFK":        ("afk",         1480133076255379671),
    "Utilities":  ("Utilities",   1480133114352107663),
    "Fun":        ("Fun",         1480133082173673615),
}

MODULES = {
    "Moderation": {
        "description": (
            "Moderation tools for keeping the server safe. All privileged commands require the special "
            "allowed role set via `!setallowroles`. Unauthorized attempts are flagged and staff is pinged. "
            "Warnings auto-mute at 3 strikes. All actions are logged to your log channels."
        ),
        "commands": [
            ("!ban <user> [reason]",
             "**Requires:** Allowed role\nPermanently bans a member. DMs them the reason."),
            ("!unban <user_id> [reason]",
             "**Requires:** Allowed role\nRevokes a ban by user ID."),
            ("!kick <user> [reason]",
             "**Requires:** Allowed role\nKicks a member from the server."),
            ("!mute <user> [duration] [reason]",
             "**Requires:** Allowed role\nTimes out a member. Duration: `10s`, `5m`, `2h`, `1d`. Max 28 days."),
            ("!unmute <user> [reason]",
             "**Requires:** Allowed role\nRemoves an active timeout immediately."),
            ("!warn <user> [reason]",
             "**Requires:** Manage Messages\nIssues a warning. At 3 warnings the member is auto-muted for 10 minutes."),
            ("!warnings <user>",
             "**Requires:** Manage Messages\nLists all warnings for a member with moderator and timestamp."),
            ("!delwarn <user>",
             "**Requires:** Allowed role\nDropdown selector to delete a specific warning from a member's record."),
            ("!modlogs <user>",
             "**Requires:** Manage Messages\nFull moderation history — bans, kicks, mutes, warns. Includes moderator and timestamps."),
            ("!modactions <user>",
             "**Requires:** Manage Messages\nShows all mod actions taken BY a user as a moderator."),
            ("!purge <1-500>",
             "**Requires:** Allowed role\nBulk-deletes up to 500 messages from the current channel."),
            ("!purgeuser <user> [1-500]",
             "**Requires:** Allowed role\nDeletes messages from a specific user. Defaults to 50."),
            ("!lock [channel] [reason]",
             "**Requires:** Allowed role\nPrevents @everyone from sending in a channel."),
            ("!unlock [channel] [reason]",
             "**Requires:** Allowed role\nRestores send permissions in a channel."),
        ]
    },
    "Music": {
        "description": (
            "High-quality music playback powered by Lavalink. Supports YouTube search, direct URLs, "
            "queue management, loop and autoplay modes, and volume control (0–200%). "
            "An interactive control panel with buttons is shown for every track. "
            "Bot auto-disconnects after 60 seconds of inactivity unless 24/7 mode is on."
        ),
        "commands": [
            ("!play / !p <query or URL>",
             "Searches YouTube and plays the top result, or loads a direct URL. Adds to queue if already playing."),
            ("!stop / !s",
             "Stops playback and clears the entire queue."),
            ("!skip",
             "Skips the current track and plays the next in the queue."),
            ("!queue",
             "Shows the current playback queue (up to 15 tracks)."),
            ("!loop",
             "Toggles loop mode. When on, the current track repeats indefinitely."),
            ("!volume / !v <0-200>",
             "Sets the playback volume. 100 is default, 200 is max."),
            ("!autoplay / !ap",
             "Toggles autoplay. Automatically queues a related track when the queue ends."),
            ("!247",
             "Toggles 24/7 mode. Bot stays in VC even when idle."),
            ("!join / !j",
             "Connects the bot to your current voice channel."),
            ("!disconnect / !d",
             "Disconnects the bot from voice and clears the queue."),
            ("!ytsearch / !yt <query>",
             "Searches YouTube and shows 5 results. Reply with a number (1–5) to play your selection."),
        ]
    },
    "Voice": {
        "description": (
            "Voice channel management tools. VC bans are persistently enforced — "
            "banned members are automatically kicked the moment they join any voice channel. "
            "`!vcmoveall` works even if you are not in a voice channel yourself."
        ),
        "commands": [
            ("!vcmoveall <dest> [source]",
             "**Requires:** Move Members\nMoves all members from source VC to destination. Defaults to your current VC."),
            ("!vckick <user> [reason]",
             "**Requires:** Move Members\nRemoves a member from their current voice channel."),
            ("!vcban <user> [reason]",
             "**Requires:** Administrator\nBans a member from all voice channels. Auto-enforced on every join."),
            ("!vcunban <user>",
             "**Requires:** Administrator\nRevokes a voice channel ban."),
            ("!adduser <user> [channel]",
             "**Requires:** Manage Channels\nGrants a member read and send access to a channel."),
        ]
    },
    "AFK": {
        "description": (
            "AFK status management. When an AFK member is mentioned, the bot notifies others of their status "
            "and how long they have been away. AFK is automatically cleared when the member next sends a message. "
            "Links are not allowed as AFK reasons."
        ),
        "commands": [
            ("!afk [reason]",
             "Sets your AFK status with an optional reason (max 200 chars, no links)."),
            ("!afkreset",
             "Manually removes your AFK status. Shows how long you were AFK."),
            ("!afkremove <user>",
             "**Server owner only** — Force-clears another member's AFK status."),
        ]
    },
    "Utilities": {
        "description": (
            "General-purpose utility commands. `!ping` shows API latency, database ping, and response time. "
            "`!autologs` auto-creates the **Incredibles Bot Logs** category with all 10 log channels in one command. "
            "`!setallowroles` controls which roles can use privileged moderation commands."
        ),
        "commands": [
            ("!ping",
             "Shows Bot Ping, Database Ping, Response Time, and Speed rating."),
            ("!serverinfo / !si",
             "Full server details: ID, owner, member counts, channels, boosts, roles, emojis, and features."),
            ("!userinfo / !ui [user]",
             "Shows username, ID, badges, join date, account creation, top role, color, and all roles."),
            ("!avatar / !av [user]",
             "Displays a member's avatar with PNG and JPG download links. Supports mentions, names, and IDs."),
            ("!banner [user]",
             "Displays a member's profile banner. Shows an error if they don't have one."),
            ("!modlogs <user>",
             "Full moderation history for a user."),
            ("!modactions <user>",
             "All actions taken BY a moderator — accountability tracking."),
            ("!autologs",
             "**Owner only** — Auto-creates the Incredibles Bot Logs category with all 10 log channels configured."),
            ("!autologs <type> [#channel]",
             "**Owner only** — Manually sets a specific log channel. Run `!autologs view` to see current settings."),
            ("!setallowroles [@role...]",
             "**Owner only** — Sets which roles can use privileged commands (ban, kick, mute, lock, purge, etc.)."),
        ]
    },
    "Fun": {
        "description": (
            "Lighthearted interaction commands. "
            "The bot deletes your command and the embed after a few seconds to keep chat clean."
        ),
        "commands": [
            ("!ben <user>",    "Fake-bans someone for laughs — no actual action taken."),
            ("!slap <user>",   "Gives someone a slap."),
            ("!punch <user>",  "Throws a punch at someone."),
            ("!cuddle <user>", "Cuddles up with someone."),
            ("!hug <user>",    "Gives someone a warm hug."),
            ("!kiss <user>",   "Sends someone a kiss."),
        ]
    },
}


def _emoji_str(module_name: str) -> str:
    data = MODULE_EMOJI_IDS.get(module_name)
    if data:
        return "<:" + data[0] + ":" + str(data[1]) + ">"
    return ""


def build_home_embed() -> discord.Embed:
    module_lines = []
    for name in MODULES:
        emoji = _emoji_str(name)
        line = (emoji + " **" + name + "**").strip()
        module_lines.append(line)

    embed = discord.Embed(
        title="Command Center",
        description=(
            "Welcome to the help menu. Select a **module** from the dropdown "
            "to view its commands and full usage details.\n\u200b\n"
            "**MODULES**\n\u200b\n" +
            "\n".join(module_lines) +
            "\n\u200b"
        ),
        color=PURPLE
    )
    gif = _get_gif("help")
    if gif:
        embed.set_image(url=gif)
    embed.set_footer(text="Select a module from the dropdown to get started")
    return embed


def build_module_embed(module_name: str) -> discord.Embed:
    data = MODULES[module_name]
    emoji = _emoji_str(module_name)
    title = (emoji + " " + module_name.upper()).strip()
    embed = discord.Embed(title=title, description=data["description"], color=PURPLE)
    embed.add_field(name="\u200b", value="**COMMANDS**", inline=False)
    for cmd, desc in data["commands"]:
        embed.add_field(name="`" + cmd + "`", value=desc, inline=False)
    gif = _get_gif("help")
    if gif:
        embed.set_image(url=gif)
    embed.set_footer(text="Use the dropdown to switch modules")
    return embed


class ModuleSelect(discord.ui.Select):
    def __init__(self):
        options = []
        for name in MODULES:
            emoji = MODULE_EMOJI_IDS.get(name)
            emoji_obj = discord.PartialEmoji(name=emoji[0], id=emoji[1]) if emoji else None
            options.append(discord.SelectOption(
                label=name,
                value=name,
                description=MODULES[name]["description"][:80].split(".")[0] + ".",
                emoji=emoji_obj,
            ))
        super().__init__(
            placeholder="Select a module to view commands...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        embed = build_module_embed(self.values[0])
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(ModuleSelect())

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help(self, ctx):
        embed = build_home_embed()
        view = HelpView()
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Help(bot))
