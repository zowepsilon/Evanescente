import discord
from discord.ext import commands

import random
import sqlite3

from utils import debuggable

class Stats(commands.Cog): # create a class for our cog that inherits from commands.Cog
    # this class is used to create a cog, which is a module that can be added to the bot

    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot
        self.repeat = True

        self.db = sqlite3.connect(self.bot.config["database"])
        self.db.autocommit = True
        self.cursor = self.db.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS MessageCounts (
                UserId int PRIMARY KEY,
                Count int
            );
        """)

    @commands.Cog.listener()
    async def on_message(self, message):
        self.cursor.execute("""
            INSERT INTO MessageCounts
            VALUES(?, 1)
            ON CONFLICT(UserId)
            DO UPDATE
            SET Count = Count + 1;
        """, [message.author.id])

    @commands.command()
    @debuggable
    async def rank(self, ctx, *, dices: str = ""):
        self.cursor.execute("""
            WITH Sorted AS (
                SELECT ROW_NUMBER() OVER (ORDER BY Count DESC) AS Rank, *
                FROM MessageCounts
            )
            SELECT Rank, Count FROM Sorted
            WHERE UserId = ?;
        """, [ctx.author.id])
        
        (rank, message_count) = self.cursor.fetchone()

        await ctx.send(f"Statistiques pour {ctx.author.mention}: {message_count} messages - Rang: #{rank}")

    @commands.command()
    @debuggable
    async def leaderboard(self, ctx, *, dices: str = ""):
        self.cursor.execute("""
            WITH Sorted AS (
                SELECT ROW_NUMBER() OVER (ORDER BY Count DESC) AS Rank, *
                FROM MessageCounts
            )
            SELECT Rank, UserId, Count FROM Sorted
            LIMIT 20;
        """)
        
        out = "## Leaderboard\n"
        for (rank, user_id, message_count) in self.cursor.fetchall():
            user = await ctx.author.guild.fetch_member(user_id)
            out += f"{rank}. {user.display_name} - {message_count} messages\n"

        await ctx.send(out)


def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Stats(bot)) # add the cog to the bot
