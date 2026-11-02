# NEXUS V1 Discord Bot

A multi-server Discord bot with verification, welcome embeds, AutoMod,
moderation, private support tickets, leveling, and reaction roles.

## Run on Replit

1. Create a Discord application and bot in the
   [Discord Developer Portal](https://discord.com/developers/applications).
2. Invite it using the `bot` and `applications.commands` scopes.
3. Add the bot token as a Replit Secret named `DISCORD_BOT_TOKEN`. Never put the
   token in source code or send it in chat.
4. In the Developer Portal, enable **Server Members Intent** and
   **Message Content Intent** for the bot.
5. Give the bot the server permissions listed below, then start the **Project**
   workflow.

The bot registers slash commands when it starts. Global commands may take a
little while to appear the first time.

## Bot permissions

Grant the bot only the permissions needed for the features you use:

- View Channels, Send Messages, Embed Links, and Read Message History
- Manage Roles (verification and reaction roles)
- Manage Channels (ticket setup and private ticket channels)
- Manage Messages (AutoMod and `/clear`)
- Moderate Members (AutoMod flood timeout and `/mute`)
- Ban Members and Kick Members (`/ban` and `/kick`)
- Add Reactions (reaction-role panels)

Keep the bot's highest role above `VERIFIED` and any reaction roles it assigns.
The bot will refuse to moderate members at or above its role hierarchy.

## Commands

### Onboarding and configuration

- `/verify` — post a persistent verification panel. Creates or reuses the
  `VERIFIED` role.
- `/welcome set channel` — choose where join embeds are sent.
- `/welcome disable` — turn off join embeds.
- `/automod configure enabled block_invites max_mentions spam_limit` — configure
  AutoMod. It starts disabled. When enabled, it can remove Discord invite
  links, excess mentions, and message floods.
- `/automod status` — view the current AutoMod settings.
- `/ticket-setup category [support_role]` — post a private ticket panel.
- `/reaction-role-setup channel role emoji` — post a reaction that adds/removes
  the selected role.

### Moderation

- `/ban member [reason]` — ban a member without deleting their message history.
- `/kick member [reason]` — remove a member from the server.
- `/clear amount` — delete 1–100 recent messages.
- `/mute member minutes [reason]` — apply a Discord timeout for 1–40,320
  minutes (up to 28 days).

Commands check the invoker's Discord permissions and role hierarchy. The bot
also checks its own permissions and position before acting.

### Members

- `/ping` — show bot latency.
- `/hello` — greet the user.
- `/rank [member]` — show a member's level and XP progress.
- `/leaderboard` — show the server's top ten members.

Leveling awards 15–25 XP at most once per member per minute. Message content is
used only for AutoMod checks and is not stored.

## Persistent data

Server settings, active tickets, XP, and reaction-role mappings are stored in
`bot_data/nexus_v1.sqlite3`. This file is excluded from Git and survives bot
process restarts in this workspace.

Set `NEXUS_DB_PATH` to use a different database file location. The bot token is
read only from `DISCORD_BOT_TOKEN`.

## Checks

Run the local checks with:

```bash
python -m unittest discover -s tests
python -m compileall -q main.py bot_app
```
