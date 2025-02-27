import discord
from discord.ext import commands

import asyncio
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
            "message": StatCounter(self.cursor, "MessageCounts", lambda msg: True),
            "feur": StatCounter(self.cursor, "FeurCounts", lambda msg: "feur" in msg),
            "bouboubou": StatCounter(self.cursor, "BouboubouCounts", lambda msg: "bouboubou" in msg),
        }

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content[0] == '?':
            return

        if message.author.bot:
            for (_, c) in self.counters.items():
                c.delete_user(message.author.id)

        for (_, c) in self.counters.items():
            c.on_message(message)

    @commands.command()
    @debuggable
    async def rank(self, ctx, *, category: str = "message", user: discord.Member = None):
        user = user if user is not None else ctx.author

        if category[-1] == 's':
            category = category[:-1]

        if category not in self.counters.keys():
            return await ctx.send(f"Unknown category `{category}`.")

        (rank, message_count) = self.counters[category].get_rank(user.id)

        await ctx.send(f"Statistiques pour {ctx.author.mention}: {message_count} {category}s - Rang: #{rank}")

    @commands.command()
    @debuggable
    async def leaderboard(self, ctx, *, category: str = "message"):
        if category[-1] == 's':
            category = category[:-1]

        if category not in self.counters.keys():
            return await ctx.send(f"Unknown category `{category}`.")
        
        leaderboard = self.counters[category].get_leaderboard()
        users = await asyncio.gather(ctx.author.guild.fetch_member(user_id) for (_, user_id, _) in leaderboard)

        out = f"## Leaderboard ({category}s)\n"
        for user, (rank, user_id, message_count) in zip(users, leaderboard):
            out += f"{rank}. {user.display_name} - {message_count} {category}s\n"

        await ctx.send(out)


def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Stats(bot)) # add the cog to the bot
