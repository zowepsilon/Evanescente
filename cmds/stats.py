import discord
from discord.ext import commands

import asyncio
import random
import sqlite3

from utils import debuggable, StatCounter, ReacCounter

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repeat = True

        self.counters = {
            "message": StatCounter(self.bot.cursor, "MessageCounts", lambda msg: True),
            "feur": StatCounter(self.bot.cursor, "FeurCounts", lambda msg: "feur" in msg.lower()),
            "bouboubou": StatCounter(self.bot.cursor, "BouboubouCounts", lambda msg: "bouboubou" in msg.lower()),
            "quoicoubeh": StatCounter(self.bot.cursor, "QuoicoubehCounts", lambda msg: "quoicoubeh" in msg.lower()),
            "cute": StatCounter(self.bot.cursor, "CuteCounts", lambda msg: any(w in msg.lower() for w in ("uwu", ":3", "rawr", "owo", "catgirl"))),
        }

        self.reac_counter = ReacCounter(self.bot.cursor, "ReactionCounts")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or len(message.content) == 0 or message.content[0] == '?':
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

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        self.bot.nickname_cache.set_nick(after.id, after.display_name)

    def get_nickname(self, ctx, user_id: int) -> str | None:
        name = self.bot.nickname_cache.get_nick(user_id)

        if name is None:
            return None

        return name[0]
        
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
    async def leaderboard(self, ctx, category: str = "message", subrange: str = None):
        if category[0] in '0123456789':
            subrange = category
            category = "message"

        if category[-1] == 's':
            category = category[:-1]

        if category not in self.counters.keys():
            return await ctx.send(f"Catégorie inconnue `{category}`. {self.category_message()}")
        
        if subrange is not None:
            subrange_spl = subrange.split("-")
            if len(subrange_spl) != 2:
                return await ctx.send(f"Range invalide `{subrange}`. Exemple de range : 5-15")
            try:
                start, end = int(subrange_spl[0]), int(subrange_spl[1])
            except ValueError:
                return await ctx.send(f"Range invalide `{subrange}`. Exemple de range : 5-15")
        
            leaderboard = self.counters[category].get_leaderboard(start, end)
        else:
            leaderboard = self.counters[category].get_leaderboard(None, 10)

        out = f"## Leaderboard ({category}s)\n"
        for rank, user_id, message_count in leaderboard:
            name = self.get_nickname(ctx, user_id)
            if name is None:
                name = "<unknown>"

            out += f"{rank}. {name} - {message_count} {category}s\n"

        await ctx.send(out)

    @commands.command()
    @debuggable
    async def reactions(self, ctx):
        if subrange is not None:
            subrange_spl = subrange.split("-")
            if len(subrange_spl) != 2:
                return await ctx.send(f"Range invalide `{subrange}`. Exemple de range : 5-15")
            try:
                start, end = int(subrange_spl[0]), int(subrange_spl[1])
            except ValueError:
                return await ctx.send(f"Range invalide `{subrange}`. Exemple de range : 5-15")
        
            leaderboard = self.reac_counter.get_leaderboard(start, end)
        else:
            leaderboard = self.reac_counter.get_leaderboard(None, 10)

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


def setup(bot):
    bot.add_cog(Stats(bot))
