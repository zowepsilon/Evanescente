from __future__ import annotations

import discord
from discord.ext import commands

from utils import debuggable, sanitize

class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repeat = True

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        print(f"{user = }")
        print(f"{reaction.count = }")
        if reaction.count != 1:
            return
        
        print(f"{reaction.emoji = }")
        if not reaction.is_custom_emoji() or reaction.emoji.id != self.bot.config["starboard_emoji_id"]:
            return
        
        starboard_channel = self.bot.get_channel(self.bot.config["starboard_id"])
        await starboard_channel.send(f"STARBOARD TEST:\n{reaction.message.content}")

def setup(bot):
    bot.add_cog(Starboard(bot))
