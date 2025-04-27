from __future__ import annotations

import re

import discord
from discord.ext import commands

from utils import debuggable, sanitize, StatCounter

perdu_regex = re.compile(r"<@(\d*)>\s*j[ ']?ai perdu", re.IGNORECASE)

class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repeat = True

        self.db = StatCounter(self.bot.cursor, "PerduCount", None)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.reference is None and len(message.mentions) == 0:
            return
        
        content = message.content.lower()
        print(repr(content))

        if message.reference is not None \
                and any(content.startswith(st) for st in ("j'ai perdu", "j ai perdu", "jai perdu")):
            author = (await message.channel.fetch_message(message.reference.message_id)).author.id
        elif (m := perdu_regex.match(content)) is not None:
            author = int(m.group(1))
        else:
            return

        if author == message.author.id:
            return

        self.db.incr(author)

    @commands.command(aliases=["jeu"])
    async def game(self, ctx, subrange: str = None):
        if subrange is not None:
            subrange_spl = subrange.split("-")
            if len(subrange_spl) != 2:
                return await ctx.send(f"Range invalide `{subrange}`. Exemple de range : 5-15")
            try:
                start, end = int(subrange_spl[0]), int(subrange_spl[1])
            except ValueError:
                return await ctx.send(f"Range invalide `{subrange}`. Exemple de range : 5-15")
        
            leaderboard = self.db.get_leaderboard(start, end)
        else:
            leaderboard = self.db.get_leaderboard(None, 10)

        out = f"## Leaderboard du Jeu\n"
        for rank, user_id, points in leaderboard:
            name = sanitize(self.bot.nickname_cache.get_nick(user_id))
            out += f"{rank}. {name} - {points} points\n"

        await ctx.send(out)



def setup(bot):
    bot.add_cog(Game(bot))


