---
name: Discord privileged intents
description: Diagnosing gateway rejection after privileged intents are enabled in the Discord Developer Portal.
---

When Discord rejects privileged intents just after the portal settings were enabled, test the bot's exact combined intent set and retry before removing required intents or shipping reduced functionality.

**Why:** During NEXUS V1 setup, initial gateway connections were rejected even after the user confirmed both intents were enabled. Separate intent checks and then the combined check later succeeded, and the normal bot startup connected without code changes.

**How to apply:** For bots that need member events and message content, preserve those intent flags. If Discord returns `PrivilegedIntentsRequired`, confirm the correct application and saved settings, test the requested set, then restart after the settings have taken effect.
