from __future__ import annotations

import discord
from discord.ext import commands

from utils import debuggable, sanitize

def split_to_chunks(text: str, chunk_size: int) -> list[str]:
    atoms = text.split(' ')

    chunks = [""]
    for a in atoms:
        if len(chunks[-1])+len(a) >= chunk_size:
            chunks.append(a)
        else:
            chunks[-1] += ' '
            chunks[-1] += a

    return chunks

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

        if len(message.attachments) > 0:
            print(message.attachments[0].content_type)

        if reaction is None \
                or reaction.count != 3 \
                or reaction.emoji.id not in self.bot.config["starboard_emoji_ids"] \
                or message.channel.id == starboard_id:
            return
        
        embed = discord.Embed()
        embed.set_author(name=message.author.name, url=message.jump_url, icon_url=message.author.display_avatar.url)
        
        if message.content != "":
            for chunk in split_to_chunks(message.content, 1000):
                embed.add_field(name="", value=chunk)

        embed.timestamp = message.created_at

        if len(message.attachments) > 0:
            embed.set_image(url=message.attachments[0].url)
        
        starboard_channel = self.bot.get_channel(starboard_id)
        message = await starboard_channel.send(embed=embed)
        await message.add_reaction(reaction.emoji)

def setup(bot):
    bot.add_cog(Starboard(bot))


