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
        starboard_id = self.bot.config["starboard_id"]

        if reaction is None or reaction.count != 1 or reaction.emoji.id != self.bot.config["starboard_emoji_id"] or message.channel_id == starboard_id:
            return
        
        embed = discord.Embed()
        embed.set_author(name=message.author.name, url=message.jump_url, icon_url=message.author.display_avatar.url)
        embed.add_field(name="", value=sanitize(message.content))

        embed.timestamp = message.created_at

        if len(message.attachments) > 0:
            embed.set_image(message.attachments[0].url)
        
        starboard_channel = self.bot.get_channel()
        message = await starboard_channel.send(embed=embed)
        await message.add_reaction(reaction.emoji)

def setup(bot):
    bot.add_cog(Starboard(bot))
