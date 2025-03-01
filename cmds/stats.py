import discord
from discord.ext import commands

import asyncio
import random
import sqlite3

from utils import debuggable, StatCounter, ReacCounter, WordCounter

cute = ["uwu", ":3", "rawr", "owo", "catgirl"]

insultes = ["chokbar", "putain", "merde", "fuck", "shit"]
tokipona = ["toki ", "pona ", "ala ", " li ", "mute ", "wile", "jan ", "kama ", "waso ", "sina "]

word_chars = "aàâäbcçĉdeéèêëfghiîïjĵjklmnoôöpqrstuùûüvwxyÿz-"
word_seps = "'()[]{}\"/,?;:.!`*_"
sep_trans = str.maketrans({c: ' ' for c in word_seps})

def words_of_message(text: str) -> list[str]:
    return [
        word for word in text.lower().translate(sep_trans).split()
        if len(word) > 1 and word[0] != '-' and word[-1] != '-' and all(c in word_chars for c in word)
    ]

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repeat = True

        self.counters = {
            "message": StatCounter(self.bot.cursor, "MessageCounts", lambda msg: True),
            "feur": StatCounter(self.bot.cursor, "FeurCounts", lambda msg: "feur" in msg.lower()),
            "bouboubou": StatCounter(self.bot.cursor, "BouboubouCounts", lambda msg: "bouboubou" in msg.lower()),
            "quoicoubeh": StatCounter(self.bot.cursor, "QuoicoubehCounts", lambda msg: "quoicoubeh" in msg.lower()),
            "cute": StatCounter(self.bot.cursor, "CuteCounts", lambda msg: any(w in msg.lower() for w in cute)),
            "insulte": StatCounter(self.bot.cursor, "InsulteCounts", lambda msg: any(w in msg.lower() for w in insultes)),
            "tokipona": StatCounter(self.bot.cursor, "TokiPonaCounts", lambda msg: any(w in msg.lower() for w in tokipona)),
        }

        self.reac_counter = ReacCounter(self.bot.cursor, "ReactionCounts")
        self.word_counter = WordCounter(self.bot.cursor, "WordCounts")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or len(message.content) == 0 or message.content[0] == '?':
            return

        for (_, c) in self.counters.items():
            c.on_message(message)
        
        if not self.bot.is_dev(message.author):
            return

        voc_channel = None
        name = None

        words = words_of_message(message.content)
        for w in words:
            if self.word_counter.exists(w):
                continue

            if voc_channel is None:
                voc_channel = self.bot.get_channel(self.bot.config["vocabulaire_id"])
                name = self.bot.nickname_cache.get_nick(user_id)

            await voc_channel.send(f"Nouveau mot : {w} - trouvé par {name}")

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
            return "<unknown>"

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
            out += f"{rank}. {name} - {message_count} {category}s\n"

        await ctx.send(out)

    @commands.command()
    @debuggable
    async def reactions(self, ctx, subrange: str = None):
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
        for (rank, emoji, count) in leaderboard:
            out += f"{rank}. {emoji} - {count} réactions\n"

        await ctx.send(out)

    @commands.command()
    @debuggable
    async def words(self, ctx, subrange: str = None):
        if subrange is not None:
            subrange_spl = subrange.split("-")
            if len(subrange_spl) != 2:
                return await ctx.send(f"Range invalide `{subrange}`. Exemple de range : 5-15")
            try:
                start, end = int(subrange_spl[0]), int(subrange_spl[1])
            except ValueError:
                return await ctx.send(f"Range invalide `{subrange}`. Exemple de range : 5-15")
        
            leaderboard = self.word_counter.get_leaderboard(start, end)
        else:
            leaderboard = self.word_counter.get_leaderboard(None, 10)

        out = f"## Leaderboard des mots\n"
        for (rank, word, count, user_id) in leaderboard:
            name = self.get_nickname(ctx, user_id)
            out += f"{rank}. {word} \\*{count} - trouvé par {name}\n"

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
