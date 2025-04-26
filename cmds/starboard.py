from __future__ import annotations

import discord
from discord.ext import commands

from utils import debuggable, sanitize

class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repeat = True

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        reaction = discord.utils.get(message.reactions, emoji=payload.emoji)
        user = payload.member

        if reaction is None or reaction.count != 1 or reaction.emoji.id != self.bot.config["starboard_emoji_id"]:
            return
        
        embed = discord.Embed()
        embed.add_field("Content", sanitize(message.content))
        embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
        embed.get_footer(text=message.jump_url)

        if len(message.attachments) > 0:
            embed.set_image(message.attachments[0].url)
        
        starboard_channel = self.bot.get_channel(self.bot.config["starboard_id"])
        await starboard_channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Starboard(bot))
