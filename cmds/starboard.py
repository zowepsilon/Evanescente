from __future__ import annotations

import asyncio

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

class BoundedSet[T]:
    def __init__(self, capacity: int):
        self.inner: list[T] = []
        self.capacity = capacity

    def add(self, x: T):
        self.inner.append(x)

        if len(self.inner) > self.capacity:
            self.inner.pop(0)

    def __contains__(self, x: T) -> bool:
        return x in self.inner


class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repeat = True
        self.starboarded: BoundedSet[int] = BoundedSet(10)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        reaction = discord.utils.get(message.reactions, emoji=payload.emoji)
        user = payload.member
        starboard_id = self.bot.config["starboard_id"]

        if reaction is None \
                or reaction.count != 3 \
                or reaction.emoji.id not in self.bot.config["starboard_emoji_ids"] \
                or message.channel.id == starboard_id \
                or message.id in self.starboarded:
            return

        self.starboarded.add(message.id)
        
        embed = discord.Embed()
        embed.set_author(name=message.author.name, url=message.jump_url, icon_url=message.author.display_avatar.url)

        content = message.content

        if message.reference is not None:
            reply = await self.bot.get_channel(payload.channel_id).fetch_message(message.reference.message_id)

            lines = ' '.join(reply.content.split('\n'))
            if len(lines) < 1000:
                author_name = sanitize(self.bot.nickname_cache.get_nick(message.author.id))
                reply_name = sanitize(self.bot.nickname_cache.get_nick(reply.author.id))

                content = f"> {reply_name} : {lines}\n{content}"


        if content != "":
            for chunk in split_to_chunks(content, 1000):
                embed.add_field(name="", value=chunk)

        embed.timestamp = message.created_at
            
        attachments = []
        if len(message.attachments) > 0:
            if message.attachments[0].content_type.split('/')[0] == "image":
                embed.set_image(url=message.attachments[0].url)
            else:
                attachments.append(await message.attachments[0].to_file())
            
            tasks = [a.to_file() for a in message.attachments[1:]]
            attachments.extend(await asyncio.gather(*tasks))
        
        starboard_channel = self.bot.get_channel(starboard_id)
        message = await starboard_channel.send(embed=embed, files=attachments)
        await message.add_reaction(reaction.emoji)

def setup(bot):
    bot.add_cog(Starboard(bot))


