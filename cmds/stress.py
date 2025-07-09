import random
from time import strftime
import hashlib

import discord
from discord.ext import commands, tasks

import aiohttp

from utils import debuggable


class Stress(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.repeat = True

    @commands.Cog.listener()
    async def on_ready(self):
        self.session = aiohttp.ClientSession()

        self.stress_loop.start()

    def cog_unload(self):
        self.stress_loop.cancel()

    @tasks.loop(minutes=1.0)
    async def stress_loop(self):
        channel = self.bot.get_channel(1366379079275642911)
        await self.check_stress(channel)

    @commands.command()
    @debuggable
    async def stress(self, ctx):
        changed = await self.check_stress(ctx)

        if not changed:
            await ctx.send("https://banques-ecoles.fr/ n'a pas changé")

    async def check_stress(self, ctx) -> bool:
        async with self.session.get("https://banques-ecoles.fr") as req:
            new_content = await req.text()

            m = hashlib.sha256()
            m.update(bytes(new_content, encoding='utf-8'))
            new_hash = m.hexdigest()

            if self.bot.config["stress_hash"] == new_hash:
                return False

            old_hash = self.bot.config["stress_hash"]
            self.bot.config["stress_hash"] = new_hash


        if old_hash == ' ':
            return False

        await ctx.send(f"<@&1391768767523979286> https://banques-ecoles.fr/ a changé\n`{old_hash}` → `{new_hash}`")

        return True



def setup(bot):
    bot.add_cog(Stress(bot))
