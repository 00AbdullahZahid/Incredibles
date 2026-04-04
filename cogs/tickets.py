import discord
from discord.ext import commands
from core.utils import log_action, success_embed, warn_embed, PURPLE
import logging

log = logging.getLogger("cogs.tickets")


class TicketCloseView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="support_close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("You need Manage Channels permission.", ephemeral=True)
        await interaction.response.send_message("Closing ticket...", ephemeral=True)
        await self.bot.db.close_ticket(interaction.channel.id)
        await log_action(self.bot, interaction.guild, "Ticket", interaction.user, interaction.user, f"Ticket closed: #{interaction.channel.name}")
        await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(TicketCloseView(self.bot))

    @commands.command(name="ticket", aliases=["supportticket"])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def ticket(self, ctx, *, topic: str = "No topic provided"):
        cat_id = await self.bot.db.get_support_cat(ctx.guild.id)
        category = ctx.guild.get_channel(cat_id) if cat_id else None

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
        }
        channel = await ctx.guild.create_text_channel(
            f"ticket-{ctx.author.name}",
            category=category,
            overwrites=overwrites,
            reason="Support ticket"
        )
        await self.bot.db.open_ticket(ctx.guild.id, ctx.author.id, channel.id, "support")

        embed = success_embed(
            "Ticket Opened",
            f"Your ticket has been created: {channel.mention}\nA moderator will be with you shortly."
        )
        await ctx.send(embed=embed, delete_after=10)

        ticket_embed = discord.Embed(
            title="Support Ticket",
            description=f"{ctx.author.mention} opened a support ticket.\nUse the button below to close it when resolved.",
            color=PURPLE
        )
        ticket_embed.add_field(name="User", value=f"{ctx.author.mention} (`{ctx.author.id}`)", inline=True)
        ticket_embed.add_field(name="Topic", value=topic, inline=True)
        view = TicketCloseView(self.bot)
        await channel.send(embed=ticket_embed, view=view)
        await log_action(self.bot, ctx.guild, "Ticket", ctx.author, ctx.guild.me, f"Support ticket opened: #{channel.name}")

    @commands.command(name="closeticket")
    @commands.has_permissions(manage_channels=True)
    async def closeticket(self, ctx):
        ticket = await self.bot.db.get_ticket_by_channel(ctx.channel.id)
        if not ticket:
            return await ctx.send(embed=warn_embed("Not a Ticket", "This channel is not a ticket."))
        await self.bot.db.close_ticket(ctx.channel.id)
        await ctx.send(embed=success_embed("Ticket Closed", "This ticket will be deleted in 5 seconds."))
        await log_action(self.bot, ctx.guild, "Ticket", ctx.author, ctx.author, f"Ticket closed: #{ctx.channel.name}")
        import asyncio
        await asyncio.sleep(5)
        await ctx.channel.delete(reason=f"Ticket closed by {ctx.author}")

    @commands.command(name="setsupportcategory")
    @commands.has_permissions(administrator=True)
    async def setsupportcategory(self, ctx, category: discord.CategoryChannel):
        if not ctx.guild.owner == ctx.author and ctx.author.id not in self.bot.owner_ids:
            return await ctx.send(embed=warn_embed("Access Denied", "Only the server owner can use this command."))
        await self.bot.db.set_support_cat(ctx.guild.id, category.id)
        embed = success_embed("Category Set", f"Support ticket category set to **{category.name}**.")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Tickets(bot))