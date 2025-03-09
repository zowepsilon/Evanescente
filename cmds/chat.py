from __future__ import annotations

import discord
from discord.ext import commands

import random

from utils import debuggable, sanitize

class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repeat = True

    @commands.Cog.listener()
    async def on_message(self, message):
        if len(message.content) == 0 or message.author.bot or message.content[0] == '?':
            return

        if self.bot.user not in message.mentions:
            return

        out = random.choice(self.bot.config["replies"])

        name = sanitize(self.bot.nickname_cache.get_nick(message.author.id))
        out = reply.replace("{user}", name)

        await message.reply(out)

    @commands.command()
    @debuggable
    async def chat_add(self, ctx, *, reply: str):
        if not self.bot.is_dev(ctx.author.id):
            return await ctx.send("You need to be a developer to do that!")

        self.bot.config["replies"].append(reply)
        await ctx.send("Réponse ajoutée !")


def setup(bot):
    bot.add_cog(Chat(bot))
