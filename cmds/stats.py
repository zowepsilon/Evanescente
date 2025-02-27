import discord
from discord.ext import commands

import random
import sqlite3

from utils import debuggable, StatCounter

class Stats(commands.Cog): # create a class for our cog that inherits from commands.Cog
    # this class is used to create a cog, which is a module that can be added to the bot

    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot
        self.repeat = True

        self.db = sqlite3.connect(self.bot.config["database"])
        self.db.autocommit = True
        self.cursor = self.db.cursor()

        self.counters = {
            "messages": StatCounter(self.cursor, "MessageCounts", lambda msg: True),
        }

    @commands.Cog.listener()
    async def on_message(self, message):
        for (_, c) in self.counters.items():
            c.on_message(message)

    @commands.command()
    @debuggable
    async def rank(self, ctx, *, category: str = "messages", user: discord.Member = None):
        user = user if user is not None else ctx.author

        if category not in self.counters.keys():
            return await ctx.send(f"Unknown category `{category}`.")

        (rank, message_count) = self.counters.get_rank(user.id)

        await ctx.send(f"Statistiques pour {ctx.author.mention}: {message_count} messages - Rang: #{rank}")

    @commands.command()
    @debuggable
    async def leaderboard(self, ctx, *, category: str = "messages"):
        if category not in self.counters.keys():
            return await ctx.send(f"Unknown category `{category}`.")

        out = "## Leaderboard\n"
        for (rank, user_id, message_count) in self.counters[category].get_leaderboard():
            user = await ctx.author.guild.fetch_member(user_id)
            out += f"{rank}. {user.display_name} - {message_count} messages\n"

        await ctx.send(out)


def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Stats(bot)) # add the cog to the bot
