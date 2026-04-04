import discord
from discord.ext import commands, tasks
import wavelink
import os
import logging
import asyncio
from core.utils import PURPLE, _get_gif, log_action

# Patch for Lavalink 4.2.x — injects channelId into voice state REST calls
# wavelink 3.4.1 doesn't send channelId but Lavalink 4.2.x requires it
_orig_update_player = wavelink.node.Node._update_player

async def _patched_update_player(self, guild_id: int, *, data: dict, replace: bool = True) -> dict:
    if 'voice' in data:
        player = self.get_player(guild_id)
        if player and getattr(player, 'channel', None):
            data['voice']['channelId'] = str(player.channel.id)
            logging.getLogger("cogs.music").info("Injected channelId=%s into voice update", player.channel.id)
        else:
            logging.getLogger("cogs.music").warning("Could not inject channelId — player=%s channel=%s", player, getattr(player, 'channel', None))
    return await _orig_update_player(self, guild_id, data=data, replace=replace)

wavelink.node.Node._update_player = _patched_update_player


log = logging.getLogger("cogs.music")

# Custom server emojis
E_PAUSE      = "<:pause:1480133099122593875>"
E_PLAY       = "<:Play:1480133100770955274>"
E_PLAY2      = "<:play2:1480133102755123303>"
E_SKIP       = "<:skip:1480133106638786580>"
E_STOP       = "<:stop:1480133108631076904>"
E_STOP2      = "<:stop2:1480133110761787392>"
E_LOOP       = "<:loop:1480133091308736643>"
E_LOOP2      = "<:autoplay:1481854207823843511>"
E_MUSIC      = "<:music:1480133097306460180>"
E_LEAVE      = "<:Leave:1480133088221593703>"
E_LEAVE2     = "<:leave2:1480133089765097603>"
E_PREVSONG   = "<:prevsong:1480133086619635864>"
E_FORWARD    = "<:forward:1480133079837446144>"
E_BACKWARD   = "<:backward:1480133078016987166>"
E_VOLUP      = "<:Volumeup:1480133121985872012>"
E_VOLDOWN    = "<:volumedown:1480133120211681412>"
E_AUTOPLAY   = "<:loop2:1480133093451890822>"


class GuildMusicState:
    def __init__(self):
        self.loop: bool = False
        self.autoplay: bool = False
        self.stay_247: bool = False


class MusicControls(discord.ui.View):
    def __init__(self, cog, guild_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id

    def _player(self) -> wavelink.Player | None:
        guild = self.cog.bot.get_guild(self.guild_id)
        vc = guild.voice_client if guild else None
        return vc if isinstance(vc, wavelink.Player) else None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        player = self._player()
        if not player:
            await interaction.response.send_message("No active player.", ephemeral=True)
            return False
        if not interaction.user.voice or interaction.user.voice.channel != player.channel:
            await interaction.response.send_message("Join the bot's voice channel first.", ephemeral=True)
            return False
        return True

    def _btn_embed(self, title: str, desc: str = None) -> discord.Embed:
        return discord.Embed(title=title, description=desc, color=PURPLE)

    # Row 0 — Playback controls
    @discord.ui.button(label="Prev", emoji=discord.PartialEmoji(name="prevsong", id=1480133086619635864), style=discord.ButtonStyle.secondary, row=0)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=self._btn_embed("No Previous Track", "There is no previous track to go back to."), ephemeral=True)

    @discord.ui.button(label="Pause", emoji=discord.PartialEmoji(name="pause", id=1480133099122593875), style=discord.ButtonStyle.secondary, row=0)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self._player()
        await player.pause(not player.paused)
        if player.paused:
            button.label = "Resume"
            button.emoji = discord.PartialEmoji(name="play2", id=1480133102755123303)
            button.style = discord.ButtonStyle.secondary
        else:
            button.label = "Pause"
            button.emoji = discord.PartialEmoji(name="pause", id=1480133099122593875)
            button.style = discord.ButtonStyle.primary
        status = "Paused" if player.paused else "Resumed"
        emoji = E_PAUSE if not player.paused else E_PLAY2
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(embed=self._btn_embed(f"{emoji} {status}", f"Playback has been {status.lower()}."), ephemeral=True)

    @discord.ui.button(label="Skip", emoji=discord.PartialEmoji(name="skip", id=1480133106638786580), style=discord.ButtonStyle.secondary, row=0)
    async def skip_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self._player()
        await player.stop()
        await interaction.response.send_message(embed=self._btn_embed(f"{E_SKIP} Skipped", "Skipped to the next track."), ephemeral=True)

    @discord.ui.button(label="Leave", emoji=discord.PartialEmoji(name="leave2", id=1480133089765097603), style=discord.ButtonStyle.secondary, row=0)
    async def disconnect_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self._player()
        await player.disconnect()
        await interaction.response.send_message(embed=self._btn_embed(f"{E_LEAVE2} Disconnected", "Left the voice channel."), ephemeral=True)

    # Row 1 — Modes & volume
    @discord.ui.button(label="Vol-", emoji=discord.PartialEmoji(name="vdown", id=1480133116248068096), style=discord.ButtonStyle.secondary, row=1)
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self._player()
        new_vol = max(0, player.volume - 10)
        await player.set_volume(new_vol)
        await interaction.response.send_message(embed=self._btn_embed(f"{E_VOLDOWN} Volume Down", f"Volume set to **{new_vol}%**"), ephemeral=True)

    @discord.ui.button(label="Vol+", emoji=discord.PartialEmoji(name="vup", id=1480133124011724981), style=discord.ButtonStyle.secondary, row=1)
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self._player()
        new_vol = min(200, player.volume + 10)
        await player.set_volume(new_vol)
        await interaction.response.send_message(embed=self._btn_embed(f"{E_VOLUP} Volume Up", f"Volume set to **{new_vol}%**"), ephemeral=True)

    @discord.ui.button(label="Loop", emoji=discord.PartialEmoji(name="loop", id=1480133091308736643), style=discord.ButtonStyle.secondary, row=1)
    async def loop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = self.cog.get_state(interaction.guild_id)
        state.loop = not state.loop
        button.style = discord.ButtonStyle.success if state.loop else discord.ButtonStyle.secondary
        button.emoji = discord.PartialEmoji(name="autoplay", id=1481854207823843511) if state.loop else discord.PartialEmoji(name="loop", id=1480133091308736643)
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(embed=self._btn_embed(f"{E_LOOP} Loop {'ON' if state.loop else 'OFF'}", f"Loop mode has been {'enabled' if state.loop else 'disabled'}."), ephemeral=True)

    @discord.ui.button(label="Autoplay", emoji=discord.PartialEmoji(name="autoplay", id=1481854207823843511), style=discord.ButtonStyle.secondary, row=1)
    async def autoplay_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = self.cog.get_state(interaction.guild_id)
        state.autoplay = not state.autoplay
        button.style = discord.ButtonStyle.success if state.autoplay else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(embed=self._btn_embed(f"{E_LOOP2} Autoplay {'ON' if state.autoplay else 'OFF'}", f"Autoplay has been {'enabled' if state.autoplay else 'disabled'}."), ephemeral=True)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_states: dict = {}
        self.node_recovery.start()

    def cog_unload(self):
        self.node_recovery.cancel()

    def get_state(self, guild_id: int) -> GuildMusicState:
        if guild_id not in self.guild_states:
            self.guild_states[guild_id] = GuildMusicState()
        return self.guild_states[guild_id]

    @tasks.loop(seconds=30)
    async def node_recovery(self):
        try:
            wavelink.Pool.get_node()
        except Exception:
            try:
                host     = os.getenv("LAVALINK_HOST", "127.0.0.1")
                port     = int(os.getenv("LAVALINK_PORT", 2333))
                password = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")
                secure   = os.getenv("LAVALINK_SECURE", "false").lower() == "true"
                scheme   = "https" if secure or port == 443 else "http"
                uri      = f"{scheme}://{host}" if port in (443, 80) else f"{scheme}://{host}:{port}"
                node     = wavelink.Node(uri=uri, password=password, heartbeat=15.0)
                await wavelink.Pool.connect(nodes=[node], client=self.bot, cache_capacity=100)
            except Exception as e:
                log.warning("Node recovery failed: %s", e)

    @node_recovery.before_loop
    async def before_recovery(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        log.info("Lavalink node ready: %s | resumed: %s", payload.node.identifier, payload.resumed)

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player):
        state = self.get_state(player.guild.id)
        if state.stay_247:
            return
        if not player.playing and player.queue.is_empty:
            await player.disconnect()

    def _embed(self, title, desc=None) -> discord.Embed:
        return discord.Embed(title=title, description=desc, color=PURPLE)

    def _now_playing_embed(self, track, state: GuildMusicState) -> discord.Embed:
        dur = f"{track.length // 60000:02}:{(track.length % 60000) // 1000:02}"
        status_parts = []
        if state.loop:     status_parts.append(f"{E_LOOP} Loop")
        if state.autoplay: status_parts.append(f"{E_LOOP2} Autoplay")
        if state.stay_247: status_parts.append("♾ 24/7")
        status = " | ".join(status_parts) if status_parts else "Normal"

        embed = discord.Embed(title=f"{E_MUSIC} Now Playing", color=PURPLE)
        embed.add_field(name="Track", value=f"**{track.title}**", inline=False)
        embed.add_field(name="Artist", value=track.author or "Unknown", inline=True)
        embed.add_field(name="Duration", value=f"`{dur}`", inline=True)
        embed.add_field(name="Mode", value=status, inline=True)
        if hasattr(track, "artwork") and track.artwork:
            embed.set_thumbnail(url=track.artwork)
        gif = _get_gif("music")
        if gif:
            embed.set_image(url=gif)
        return embed

    async def _get_player(self, ctx) -> wavelink.Player | None:
        vc = ctx.voice_client
        if isinstance(vc, wavelink.Player):
            return vc
        if vc is not None:
            await vc.disconnect(force=True)
            await asyncio.sleep(1)
        if not ctx.author.voice:
            await ctx.send(embed=self._embed("Voice Required", "Join a voice channel first."))
            return None
        try:
            player: wavelink.Player = await ctx.author.voice.channel.connect(
                cls=wavelink.Player, self_deaf=True, timeout=60.0
            )
            player.inactive_timeout = 60
            # Wait for Lavalink to complete UDP handshake with Discord voice servers
            await asyncio.sleep(1)
            return player
        except Exception as e:
            log.exception("Failed to connect wavelink player: %s", e)
            await ctx.send(embed=self._embed("Connection Failed", str(e)))
            return None

    async def _ensure_voice(self, ctx) -> bool:
        if not ctx.author.voice:
            await ctx.send(embed=self._embed("Voice Required", "Join a voice channel first."))
            return False
        try:
            wavelink.Pool.get_node()
        except wavelink.InvalidNodeException:
            await ctx.send(embed=self._embed("Lavalink Offline", "Music server is not connected. Please wait a moment and try again."))
            return False
        return True

    async def _search(self, query: str):
        if query.startswith("http://") or query.startswith("https://"):
            return await wavelink.Playable.search(query)
        return await wavelink.Playable.search(f"ytsearch:{query}")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player = payload.player
        track = payload.track
        if not player:
            return
        state = self.get_state(player.guild.id)
        try:
            if state.loop:
                await player.play(track)
                return
            if not player.queue.is_empty:
                next_track = player.queue.get()
                await player.play(next_track)
                return
            if state.autoplay:
                results = await self._search(track.title)
                if results:
                    await player.play(results[0])
                    return
            if not state.stay_247:
                await asyncio.sleep(30)
                if not player.playing:
                    await player.disconnect()
        except Exception as e:
            log.error("Track end error: %s", e)

    # ── Commands ───────────────────────────────────────────────────────────────

    @commands.command(name="join", aliases=["j"])
    async def join(self, ctx):
        if not await self._ensure_voice(ctx):
            return
        player = await self._get_player(ctx)
        if player:
            await ctx.send(embed=self._embed(f"{E_MUSIC} Connected", f"Joined {ctx.author.voice.channel.mention}"))

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *, query: str):
        if not await self._ensure_voice(ctx):
            return
        try:
            player = await self._get_player(ctx)
            if not player:
                return
            state = self.get_state(ctx.guild.id)
            tracks = await self._search(query)
            if not tracks:
                return await ctx.send(embed=self._embed("No Results", "No tracks found for that query."))
            track = tracks[0] if isinstance(tracks, list) else tracks
            if not player.playing:
                log.info("Sending play request to Lavalink - track: %s, node: %s, guild: %s", track.title, player.node.identifier, ctx.guild.id)
                await player.play(track)
                log.info("Play request sent successfully")
                embed = self._now_playing_embed(track, state)
                view = MusicControls(self, ctx.guild.id)
                await ctx.send(embed=embed, view=view)
                await log_action(self.bot, ctx.guild, "Music", None, ctx.author, f"Playing: {track.title}")
            else:
                await player.queue.put_wait(track)
                dur = f"{track.length // 60000:02}:{(track.length % 60000) // 1000:02}"
                embed = self._embed(f"{E_MUSIC} Added to Queue", f"**{track.title}**")
                embed.add_field(name="Duration", value=f"`{dur}`", inline=True)
                embed.add_field(name="Position", value=f"#{len(player.queue)}", inline=True)
                if hasattr(track, "artwork") and track.artwork:
                    embed.set_thumbnail(url=track.artwork)
                await ctx.send(embed=embed)
        except Exception as e:
            log.exception("Play error: %s", e)
            await ctx.send(embed=self._embed("Playback Error", str(e)))

    @commands.command(name="stop", aliases=["s"])
    async def stop(self, ctx):
        player = ctx.voice_client
        if not isinstance(player, wavelink.Player):
            return await ctx.send(embed=self._embed("Not Playing", "Nothing is playing."))
        player.queue.clear()
        await player.stop()
        await ctx.send(embed=self._embed(f"{E_STOP} Stopped", "Playback stopped and queue cleared."))

    @commands.command(name="skip")
    async def skip(self, ctx):
        player = ctx.voice_client
        if not isinstance(player, wavelink.Player):
            return await ctx.send(embed=self._embed("Not Playing", "Nothing is playing."))
        await player.stop()
        await ctx.send(embed=self._embed(f"{E_SKIP} Skipped", "Track skipped."))

    @commands.command(name="queue")
    async def queue(self, ctx):
        player = ctx.voice_client
        if not isinstance(player, wavelink.Player) or player.queue.is_empty:
            return await ctx.send(embed=self._embed("Queue", "The queue is empty."))
        tracks = list(player.queue)[:15]
        desc = "\n".join(f"`{i+1}.` {t.title}" for i, t in enumerate(tracks))
        embed = self._embed(f"{E_MUSIC} Queue", desc)
        embed.set_footer(text=f"{len(player.queue)} track(s) in queue")
        await ctx.send(embed=embed)

    @commands.command(name="loop")
    async def loop(self, ctx):
        state = self.get_state(ctx.guild.id)
        state.loop = not state.loop
        await ctx.send(embed=self._embed(f"{E_LOOP} Loop", f"Loop {'enabled' if state.loop else 'disabled'}."))

    @commands.command(name="volume", aliases=["v"])
    async def volume(self, ctx, value: int):
        player = ctx.voice_client
        if not isinstance(player, wavelink.Player):
            return await ctx.send(embed=self._embed("Not Playing", "Nothing is playing."))
        if not 0 <= value <= 200:
            return await ctx.send(embed=self._embed("Invalid", "Volume must be 0-200."))
        await player.set_volume(value)
        await ctx.send(embed=self._embed(f"{E_VOLUP} Volume", f"Volume set to **{value}%**"))

    @commands.command(name="autoplay", aliases=["ap"])
    async def autoplay(self, ctx):
        state = self.get_state(ctx.guild.id)
        state.autoplay = not state.autoplay
        await ctx.send(embed=self._embed(f"{E_LOOP2} Autoplay", f"Autoplay {'enabled' if state.autoplay else 'disabled'}."))

    @commands.command(name="247")
    async def mode247(self, ctx):
        state = self.get_state(ctx.guild.id)
        state.stay_247 = not state.stay_247
        await ctx.send(embed=self._embed("♾ 24/7 Mode", f"24/7 Mode {'enabled' if state.stay_247 else 'disabled'}."))

    @commands.command(name="disconnect", aliases=["d"])
    async def disconnect(self, ctx):
        player = ctx.voice_client
        if not player:
            return await ctx.send(embed=self._embed("Not Connected", "Bot is not in a voice channel."))
        await player.disconnect()
        await ctx.send(embed=self._embed(f"{E_LEAVE} Disconnected", "Left the voice channel."))

    @commands.command(name="ytsearch", aliases=["yt"])
    async def ytsearch(self, ctx, *, query: str):
        if not await self._ensure_voice(ctx):
            return
        tracks = await self._search(query)
        if not tracks:
            return await ctx.send(embed=self._embed("No Results", "No tracks found."))
        results = tracks[:5]
        desc = "\n".join(
            f"`{i+1}.` {t.title} — `{t.length // 60000:02}:{(t.length % 60000) // 1000:02}`"
            for i, t in enumerate(results)
        )
        embed = self._embed(f"{E_MUSIC} YouTube Search Results", desc)
        embed.set_footer(text="Reply with a number 1–5 to play a track")
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            index = int(msg.content) - 1
            if not 0 <= index < len(results):
                return await ctx.send(embed=self._embed("Invalid", "Please pick a number from the list."))
            player = await self._get_player(ctx)
            if not player:
                return
            track = results[index]
            state = self.get_state(ctx.guild.id)
            if not player.playing:
                await player.play(track)
                await ctx.send(embed=self._now_playing_embed(track, state), view=MusicControls(self, ctx.guild.id))
            else:
                await player.queue.put_wait(track)
                await ctx.send(embed=self._embed(f"{E_MUSIC} Added to Queue", f"**{track.title}**"))
        except asyncio.TimeoutError:
            await ctx.send(embed=self._embed("Timed Out", "No selection made."))


async def setup(bot):
    await bot.add_cog(Music(bot))
