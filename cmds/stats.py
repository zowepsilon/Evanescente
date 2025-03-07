import discord
from discord.ext import commands

import asyncio
import random
import sqlite3

from utils import debuggable, StatCounter, ReacCounter, WordCounter, sanitize, words_of_message, cute, insultes, tokipona


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

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or len(message.content) == 0 or message.content[0] == '?':
            return

        for (_, c) in self.counters.items():
            c.on_message(message)
        
        voc_channel = None
        name = None

        words = words_of_message(message.content)

        tasks = []

        found_count = 0
        for w in words:
            if self.bot.word_counter.exists(w):
                continue

            found_count += 1

            if voc_channel is None:
                voc_channel = self.bot.get_channel(self.bot.config["vocabulaire_id"])
                name = sanitize(self.bot.nickname_cache.get_nick(message.author.id))

            tasks.append(voc_channel.send(f"Nouveau mot : `{w}` - trouvé par {name}"))

        self.bot.word_counter.add_words(words, message.author.id)

        if found_count > 10:
            await message.add_reaction("🤓")

        await asyncio.gather(*tasks)

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

    @commands.command()
    @debuggable
    async def rank(self, ctx, *, user: discord.Member = None):
        user = user if user is not None else ctx.author

        out = f"### Statistiques pour {user.mention}: \n"
        for category in self.counters.keys():
            try:
                (rank, message_count) = self.counters[category].get_rank(user.id)
            except TypeError:
                continue

            out += f"- {message_count} {category}s - Rang: #{rank}\n"
        try:
            (rank, count) = self.bot.word_counter.get_user_rank(user.id)
            out += f"- {count} mots trouvés - Rang: #{rank}"
        except TypeError:
            pass

        await ctx.send(out)

    @commands.command(aliases=["lb"])
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
            name = sanitize(self.bot.nickname_cache.get_nick(user_id))
            out += f"{rank}. {name} - {message_count} {category}s\n"

        await ctx.send(out)


    @commands.command()
    @debuggable
    async def explorers(self, ctx, subrange: str = None):
        if subrange is not None:
            subrange_spl = subrange.split("-")
            if len(subrange_spl) != 2:
                return await ctx.send(f"Range invalide `{subrange}`. Exemple de range : 5-15")
            try:
                start, end = int(subrange_spl[0]), int(subrange_spl[1])
            except ValueError:
                return await ctx.send(f"Range invalide `{subrange}`. Exemple de range : 5-15")
        
            leaderboard = self.bot.word_counter.get_user_leaderboard(start, end)
        else:
            leaderboard = self.bot.word_counter.get_user_leaderboard(None, 10)

        out = f"## Leaderboard d'exploration\n"
        for rank, user_id, count in leaderboard:
            name = sanitize(self.bot.nickname_cache.get_nick(user_id))
            out += f"{rank}. {name} - {count} mots trouvés\n"

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
        
            leaderboard = self.bot.word_counter.get_word_leaderboard(start, end)
        else:
            leaderboard = self.bot.word_counter.get_word_leaderboard(None, 10)

        out = f"## Leaderboard des mots\n"
        for (rank, word, count, user_id) in leaderboard:
            name = sanitize(self.bot.nickname_cache.get_nick(user_id))
            out += f"{rank}. `{word}` - utilisé {count} fois, trouvé par {name}\n"

        await ctx.send(out)

    @commands.command()
    @debuggable
    async def word(self, ctx, word: str):
        word = sanitize(word.lower())
        try:
            (rank, count, first_user_id) = self.bot.word_counter.get_word_rank(word)
        except TypeError:
            return await ctx.send(f"Mot inconnu: `{word}`")
        
        name = sanitize(self.bot.nickname_cache.get_nick(first_user_id))
        await ctx.send(f"Statistiques pour `{word}`: #{rank} - utilisé {count} fois, trouvé par {name}")
    
    def category_message(self):
        out = "Les catégories sont "
        cat = list(self.counters.keys())

        for c in cat[:-1]:
            out += c + ", "

        out += f"et {cat[-1]}."

        return out


def setup(bot):
    bot.add_cog(Stats(bot))
