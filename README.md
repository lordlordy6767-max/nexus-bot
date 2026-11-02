# Discord Bot

A Python starter bot built with `discord.py`. It registers two Discord slash
commands:

- `/ping` — replies with the bot's latency.
- `/hello` — greets the person who used the command.

## Run it on Replit

1. Create an application and bot in the [Discord Developer Portal](https://discord.com/developers/applications).
2. Invite the bot to your server with the `bot` and `applications.commands` scopes.
3. Add the bot token as a Replit Secret named `DISCORD_BOT_TOKEN`. Do not put
   the token in this file or commit it to the project.
4. Start the **Project** workflow.

The bot registers its slash commands when it starts. Discord may take a little
while to show global commands the first time.

## Add commands

Add new slash commands in `main.py` using the existing `@bot.tree.command`
examples. They are synchronized with Discord when the bot starts.
