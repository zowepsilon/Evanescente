import discord
from discord.ext import commands

import asyncio
import random
import sqlite3

from utils import debuggable, StatCounter, ReacCounter

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
            "feur": StatCounter(self.cursor, "FeurCounts", lambda msg: "feur" in msg.lower()),
            "bouboubou": StatCounter(self.cursor, "BouboubouCounts", lambda msg: "bouboubou" in msg.lower()),
            "quoicoubeh": StatCounter(self.cursor, "QuoicoubehCounts", lambda msg: "quoicoubeh" in msg.lower()),
    
        }

        self.reac_counter = ReacCounter(self.cursor, "ReactionCounts")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.content[0] == '?':
            return

        for (_, c) in self.counters.items():
            c.on_message(message)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if isinstance(reaction.emoji, str):
            self.reac_counter.incr(reaction.emoji)
        elif isinstance(reaction.emoji, discord.Emoji):
            self.reac_counter.incr(str(reaction.emoji))

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if isinstance(reaction.emoji, str):
            self.reac_counter.decr(reaction.emoji)
        elif isinstance(reaction.emoji, discord.Emoji):
            self.reac_counter.decr(str(reaction.emoji))

    @commands.command()
    @debuggable
    async def rank(self, ctx, *, category: str = "message", user: discord.Member = None):
        user = user if user is not None else ctx.author

        if category[-1] == 's':
            category = category[:-1]

        if category not in self.counters.keys():
            return await ctx.send(f"Unknown category `{category}`. {self.category_message()}")

        (rank, message_count) = self.counters[category].get_rank(user.id)

        await ctx.send(f"Statistiques pour {ctx.author.mention}: {message_count} {category}s - Rang: #{rank}")

    @commands.command()
    @debuggable
    async def leaderboard(self, ctx, *, category: str = "message"):
        if category[-1] == 's':
            category = category[:-1]

        if category not in self.counters.keys():
            return await ctx.send(f"Catégorie inconnue `{category}`. {self.category_message()}")
        
        leaderboard = self.counters[category].get_leaderboard()
        users = await asyncio.gather(*(ctx.author.guild.fetch_member(user_id) for (_, user_id, _) in leaderboard))

        out = f"## Leaderboard ({category}s)\n"
        for user, (rank, user_id, message_count) in zip(users, leaderboard):
            out += f"{rank}. {user.display_name} - {message_count} {category}s\n"

        await ctx.send(out)

    @commands.command()
    @debuggable
    async def reactions(self, ctx):
        out = f"## Leaderboard des réactions\n"
        for (rank, emoji, count) in self.reac_counter.get_leaderboard():
            out += f"{rank}. {emoji} - {count} réactions\n"

        await ctx.send(out)

    def category_message(self):
        out = "Les catégories sont "
        cat = list(self.counters.keys())

        for c in cat[:-1]:
            out += c + ", "

        out += f"et {cat[-1]}."

        return out


def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Stats(bot)) # add the cog to the bot
