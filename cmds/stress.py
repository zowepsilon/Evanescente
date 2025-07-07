import random
from time import strftime

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

        if "stress_hash" not in self.bot.config:
            self.bot.config["stress_hash"] = 0

    @tasks.loop(minutes=5.0)
    async def check_stress(self):
        async with self.session.get("https://banques-ecoles.fr") as req:
            new_content = await req.text()
            new_hash = hash(new_content)

            if self.bot.config["stress_hash"] == new_hash:
                return

            old_hash = self.bot.config["stress_hash"]
            self.bot.config["stress_hash"] = new_hash

        channel = self.bot.get_channel(1366379079275642911)

        await channel.send(f"<@&1391768767523979286> https://banques-ecoles.fr/ a changé : `{old_hash}` → `{new_hash}`")



def setup(bot):
    bot.add_cog(Stress(bot))
