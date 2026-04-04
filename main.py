import discord
from discord.ext import commands
import os
import logging
import wavelink
from dotenv import load_dotenv
from core.database import Database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(BASE_DIR, "logs")
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, "bot.log")),
        logging.StreamHandler()
    ]
)

load_dotenv(os.path.join(BASE_DIR, ".env"))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.presences = True


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=intents,
            help_command=None,
            case_insensitive=True,
            chunk_guilds_at_startup=True,
        )
        owner_str = os.getenv("OWNER_IDS", "")
        self.owner_ids = set(map(int, owner_str.split(","))) if owner_str else set()
        self.db = Database()

    async def setup_hook(self):
        await self.db.init()

        # Connect Lavalink node before cogs load
        host     = os.getenv("LAVALINK_HOST", "127.0.0.1")
        port     = int(os.getenv("LAVALINK_PORT", 2333))
        password = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")
        secure   = os.getenv("LAVALINK_SECURE", "false").lower() == "true"
        scheme   = "https" if secure or port == 443 else "http"
        if (scheme == "https" and port == 443) or (scheme == "http" and port == 80):
            uri = f"{scheme}://{host}"
        else:
            uri = f"{scheme}://{host}:{port}"
        try:
            node = wavelink.Node(
                uri=uri,
                password=password,
                heartbeat=15.0,
            )
            await wavelink.Pool.connect(nodes=[node], client=self, cache_capacity=100)
            logging.getLogger("bot").info("Lavalink connected: %s", uri)
        except Exception as e:
            logging.getLogger("bot").warning("Lavalink connection failed: %s", e)

        cogs_dir = os.path.join(BASE_DIR, "cogs")
        for fn in sorted(os.listdir(cogs_dir)):
            if fn.endswith(".py") and not fn.startswith("_"):
                ext = "cogs." + fn[:-3]
                try:
                    await self.load_extension(ext)
                    logging.getLogger("bot").info("Loaded: %s", ext)
                except Exception as e:
                    logging.getLogger("bot").error("Failed %s: %s", ext, e)

    async def on_ready(self):
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="The Incredibles | /incredibles"
            )
        )
        logging.getLogger("bot").info("Ready as %s (%s)", self.user, self.user.id)


bot = Bot()


@bot.event
async def on_command_error(ctx, error):
    from core.utils import error_embed, warn_embed, PURPLE, YELLOW, _get_gif
    import discord

    # Unwrap CommandInvokeError
    if isinstance(error, commands.CommandInvokeError):
        error = error.original

    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.NoPrivateMessage):
        return await ctx.send(embed=warn_embed(
            "Server Only",
            "This command can only be used inside a server.",
            gif_key="error"
        ))

    if isinstance(error, commands.CheckFailure):
        return  # handled per-command

    if isinstance(error, commands.MissingPermissions):
        perms = ", ".join(p.replace("_", " ").title() for p in error.missing_permissions)
        return await ctx.send(embed=warn_embed(
            "Missing Permissions",
            "You need the following permission(s) to use this command:\n`" + perms + "`",
            gif_key="error"
        ))

    if isinstance(error, commands.BotMissingPermissions):
        perms = ", ".join(p.replace("_", " ").title() for p in error.missing_permissions)
        return await ctx.send(embed=error_embed(
            "Bot Missing Permissions",
            "I need the following permission(s) to do that:\n`" + perms + "`",
            gif_key="error"
        ))

    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(
            title="Slow Down",
            description="This command is on cooldown. Try again in `" + str(round(error.retry_after, 1)) + "s`.",
            color=YELLOW
        )
        gif = _get_gif("error")
        if gif:
            embed.set_image(url=gif)
        return await ctx.send(embed=embed, delete_after=5)

    if isinstance(error, (commands.MemberNotFound, commands.UserNotFound)):
        return await ctx.send(embed=warn_embed(
            "Member Not Found",
            "Could not find that member. Make sure you're mentioning them correctly or using their exact ID.",
            gif_key="error"
        ))

    if isinstance(error, commands.RoleNotFound):
        return await ctx.send(embed=warn_embed(
            "Role Not Found",
            "Could not find that role. Check the spelling or mention the role directly.",
            gif_key="error"
        ))

    if isinstance(error, commands.ChannelNotFound):
        return await ctx.send(embed=warn_embed(
            "Channel Not Found",
            "Could not find that channel.",
            gif_key="error"
        ))

    if isinstance(error, commands.BadArgument):
        return await ctx.send(embed=warn_embed(
            "Invalid Argument",
            str(error) + "\nUse `!help` for correct command usage.",
            gif_key="error"
        ))

    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(embed=warn_embed(
            "Missing Argument",
            "Required argument missing: `" + error.param.name + "`\nUse `!help` for correct usage.",
            gif_key="error"
        ))

    if isinstance(error, commands.TooManyArguments):
        return await ctx.send(embed=warn_embed(
            "Too Many Arguments",
            "You provided too many arguments.\nUse `!help` for correct usage.",
            gif_key="error"
        ))

    if isinstance(error, discord.Forbidden):
        return await ctx.send(embed=error_embed(
            "Permission Denied",
            "I don't have permission to do that. Check my role position and channel permissions.",
            gif_key="error"
        ))

    if isinstance(error, discord.HTTPException):
        return await ctx.send(embed=error_embed(
            "Discord Error",
            "An HTTP error occurred: " + str(error.text),
            gif_key="error"
        ))

    logging.getLogger("bot").exception("Unhandled error in %s: %s", ctx.command, error)
    await ctx.send(embed=error_embed(
        "Internal Error",
        "An unexpected error occurred. Please try again.\n`" + type(error).__name__ + ": " + str(error) + "`",
        gif_key="error"
    ))


if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logging.getLogger("bot").critical("DISCORD_TOKEN not found in .env!")
    else:
        bot.run(token)