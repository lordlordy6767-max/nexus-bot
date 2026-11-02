from __future__ import annotations

import logging

import discord
from discord import app_commands

from bot_app.branding import PURPLE, brand_embed
from bot_app.storage import BotStore

logger = logging.getLogger("discord_bot.tickets")


class TicketPanelView(discord.ui.View):
    def __init__(self, store: BotStore) -> None:
        super().__init__(timeout=None)
        self.store = store

    @discord.ui.button(
        label="Open a ticket",
        emoji="🎫",
        style=discord.ButtonStyle.primary,
        custom_id="nexus:ticket:open",
    )
    async def open_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Tickets can only be opened inside a server.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        existing = await self.store.get_open_ticket(guild.id, member.id)
        if existing is not None:
            existing_channel = guild.get_channel(int(existing["channel_id"]))
            if isinstance(existing_channel, discord.TextChannel):
                await interaction.followup.send(
                    f"You already have an open ticket: {existing_channel.mention}",
                    ephemeral=True,
                )
                return
            await self.store.close_ticket(int(existing["channel_id"]))

        settings = await self.store.get_settings(guild.id)
        category_id = settings.get("ticket_category_id")
        category = guild.get_channel(int(category_id)) if category_id else None
        if not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send(
                "Tickets are not configured yet. Ask an administrator to run "
                "`/ticket-setup`.",
                ephemeral=True,
            )
            return

        bot_user = interaction.client.user
        bot_member = guild.get_member(bot_user.id) if bot_user is not None else None
        if bot_member is None or not bot_member.guild_permissions.manage_channels:
            await interaction.followup.send(
                "I need the Manage Channels permission to open tickets.",
                ephemeral=True,
            )
            return

        overwrites: dict[
            discord.Role | discord.Member,
            discord.PermissionOverwrite,
        ] = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
            ),
            bot_member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
            ),
        }
        support_role_id = settings.get("support_role_id")
        support_role = guild.get_role(int(support_role_id)) if support_role_id else None
        if support_role is not None:
            overwrites[support_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
            )

        try:
            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{member.id}",
                category=category,
                overwrites=overwrites,
                topic=f"NEXUS ticket for user {member.id}",
                reason=f"NEXUS V1 ticket opened by {member}",
            )
            try:
                await self.store.create_ticket(
                    guild.id,
                    ticket_channel.id,
                    member.id,
                )
            except Exception:
                await ticket_channel.delete(
                    reason="Ticket record could not be saved"
                )
                raise

            await ticket_channel.send(
                content=member.mention,
                embed=brand_embed(
                    "Support ticket opened",
                    "Describe what you need help with. A staff member will be "
                    "with you soon.",
                    color=PURPLE,
                ),
                view=TicketCloseView(self.store),
                allowed_mentions=discord.AllowedMentions(users=True),
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "I could not create the private ticket channel. Check my "
                "Manage Channels and View Channel permissions.",
                ephemeral=True,
            )
            return
        except Exception:
            logger.exception("Failed to create a ticket in guild %s", guild.id)
            await interaction.followup.send(
                "The ticket could not be saved. Please try again or contact a "
                "server moderator.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            f"Your ticket is ready: {ticket_channel.mention}",
            ephemeral=True,
        )


class TicketCloseView(discord.ui.View):
    def __init__(self, store: BotStore) -> None:
        super().__init__(timeout=None)
        self.store = store

    @discord.ui.button(
        label="Close ticket",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="nexus:ticket:close",
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        guild = interaction.guild
        channel = interaction.channel
        actor = interaction.user
        if guild is None or not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "This button only works inside a ticket channel.",
                ephemeral=True,
            )
            return

        ticket = await self.store.get_ticket_by_channel(channel.id)
        if ticket is None or ticket["closed_at"] is not None:
            await interaction.response.send_message(
                "This ticket is already closed.",
                ephemeral=True,
            )
            return

        settings = await self.store.get_settings(guild.id)
        support_role_id = settings.get("support_role_id")
        support_role = guild.get_role(int(support_role_id)) if support_role_id else None
        actor_is_support = (
            isinstance(actor, discord.Member)
            and support_role is not None
            and support_role in actor.roles
        )
        is_owner = actor.id == int(ticket["user_id"])
        is_manager = (
            isinstance(actor, discord.Member)
            and actor.guild_permissions.manage_channels
        )
        if not (is_owner or is_manager or actor_is_support):
            await interaction.response.send_message(
                "Only the ticket owner or support staff can close this ticket.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        owner = guild.get_member(int(ticket["user_id"]))
        try:
            if owner is not None:
                await channel.set_permissions(
                    owner,
                    view_channel=False,
                    send_messages=False,
                    reason=f"Ticket closed by {actor}",
                )
        except discord.Forbidden:
            await interaction.followup.send(
                "I could not close this ticket. Check my Manage Channels "
                "permission.",
                ephemeral=True,
            )
            return

        await self.store.close_ticket(channel.id)
        try:
            await channel.edit(
                name=f"closed-{int(ticket['user_id'])}",
                reason=f"Ticket closed by {actor}",
            )
        except discord.Forbidden:
            logger.warning(
                "Ticket %s was locked but could not be renamed",
                channel.id,
            )
        await interaction.followup.send(
            "Ticket closed. The requester can no longer view this channel.",
            ephemeral=True,
        )


def register_tickets(bot: discord.Client, store: BotStore) -> None:
    @bot.tree.command(
        name="ticket-setup",
        description="Create a private ticket panel.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_setup(
        interaction: discord.Interaction,
        category: discord.CategoryChannel,
        support_role: discord.Role | None = None,
    ) -> None:
        guild = interaction.guild
        channel = interaction.channel
        if guild is None or channel is None or not hasattr(channel, "send"):
            await interaction.response.send_message(
                "Run this command in a server text channel.",
                ephemeral=True,
            )
            return

        bot_member = guild.get_member(bot.user.id) if bot.user else None
        if bot_member is None or not bot_member.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "I need the Manage Channels permission to configure tickets.",
                ephemeral=True,
            )
            return
        if support_role is not None:
            actor = interaction.user
            if (
                isinstance(actor, discord.Member)
                and actor.id != guild.owner_id
                and support_role >= actor.top_role
            ):
                await interaction.response.send_message(
                    "Choose a support role below your highest role.",
                    ephemeral=True,
                )
                return

        await interaction.response.defer(ephemeral=True, thinking=True)
        await store.set_settings(
            guild.id,
            ticket_category_id=category.id,
            support_role_id=support_role.id if support_role else None,
        )
        await channel.send(
            embed=brand_embed(
                "NEXUS V1 Support",
                "Need help? Open a private ticket and our team will assist you.",
                color=PURPLE,
            ),
            view=TicketPanelView(store),
            allowed_mentions=discord.AllowedMentions.none(),
        )
        await interaction.followup.send(
            "Ticket panel deployed.",
            ephemeral=True,
        )


def register_ticket_views(bot: discord.Client, store: BotStore) -> None:
    bot.add_view(TicketPanelView(store))
    bot.add_view(TicketCloseView(store))
