from __future__ import annotations

import discord
from discord.ext import commands

import asyncio
import random
import sqlite3
from dataclasses import dataclass, field

from utils import debuggable, sanitize, words_of_message, PenduAccuracyCounter, word_chars

cute = ["uwu", ":3", "rawr", "owo", "catgirl", "bébou"]

insultes = ["chokbar", "putain", "merde", "fuck", "shit", "ptn"]
tokipona = ["toki ", "pona ", "ala ", " li ", "mute ", "wile ", "jan ", "kama ", "waso ", "sina "]

@dataclass
class PenduState:
    message: Message
    word: str
    remaining: int
    bot: Bot
    
    displayed_found: set[str] = field(default_factory=set)
    found: set[str] = field(default_factory=lambda: {'-'})
    displayed_wrong: set[str] = field(default_factory=set)
    wrong: set[str] = field(default_factory=set)

    def complete(self) -> bool:
        return all(c in self.found for c in self.word)

    def partial_word(self) -> str:
        return ''.join(c if c in self.found else '_' for c in self.word)

    def add(self, letter: str) -> bool:
        classes = [
            'aàâä', 'b', 'cçĉ', 'd', 'eéèêë', 'f', 'g', 'h', 'iîï', 
            'jĵ', 'k', 'l', 'm', 'n', 'oôö', 'p', 'q', 'r', 's', 't',
            'uùûü', 'v', 'w', 'x', 'yÿ', 'z', '-'
        ]

        for cl in classes:
            if letter not in cl:
                continue
            
            if any(c in self.word for c in cl):
                self.found.update(cl)
                self.displayed_found.add(cl[0])
                return True
            else:
                self.wrong.update(cl)
                self.displayed_wrong.add(cl[0])
                return False

    async def update(self):
        out = ""

        if self.complete():
            out += "## Gagné !\n"
        elif self.remaining == 0:
            out += "## Perdu !\n"

        if self.remaining != 0 and not self.complete():
            out += f"### Le mot est `{self.partial_word()}`.\n"
        else:
            out += f"### Le mot était `{self.word}` "

            (rank, count, first_user_id) = self.bot.word_counter.get_word_rank(self.word)
            name = sanitize(self.bot.nickname_cache.get_nick(first_user_id))

            out += f"(#{rank} - utilisé {count} fois, trouvé par {name}).\n"

        out += f"- Coups restants: {self.remaining}\n"

        out += "- Lettres trouvées : " + ''.join(sorted(list(self.displayed_found))) + '\n'
        out += "- Lettres incorrectes : " + ''.join(sorted(list(self.displayed_wrong))) + '\n'

        await self.message.edit(out)


class Pendu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repeat = True

        self.games: dict[int, PenduState] = {}
        self.db = PenduAccuracyCounter(self.bot.cursor, "PenduAccuracies")

    @commands.Cog.listener()
    async def on_message(self, message):
        if len(message.content) == 0 or message.author.bot or message.content[0] == '?':
            return

        channel = message.channel.id
        if message.channel.id not in self.games.keys():
            return

        word = self.games[channel].word
        if message.content == word:
            await message.add_reaction("✅")
            await message.add_reaction("🔥")
            
            for letter in word:
                if letter not in self.games[channel].found:
                    self.db.add_correct_letter(message.author.id)
                    self.games[channel].add(letter)

            await self.up(message.channel)
            self.games.pop(channel)

            return

        if len(message.content) != 1:
            return

        letter = message.content[0].lower()

        if letter not in word_chars:
            return

        if letter in self.games[channel].found:
            return

        if letter in self.games[channel].wrong:
            return

        if self.games[channel].add(letter):
            await message.add_reaction("✅")

            self.db.add_correct_letter(message.author.id)
            
            if self.games[channel].complete():
                await self.up(message.channel)
                self.games.pop(channel)
            else:
                await self.games[channel].update()
        else:
            self.games[channel].remaining -= 1
            await self.games[channel].update()
            await message.add_reaction("❌")

            self.db.add_wrong_letter(message.author.id)

            if self.games[channel].remaining == 0:
                await self.up(message.channel)
                self.games.pop(channel)

    @commands.group(invoke_without_command=True)
    @debuggable
    async def pendu(self, ctx):
       await ctx.send("Usage: `pendu start`, `pendu ff`")

    @pendu.command(name="start")
    @debuggable
    async def pendu_start(self, ctx, difficulty: float = 0.3):
        word = self.bot.word_counter.get_random_word()
        self.games[ctx.channel.id] = PenduState(word=word, remaining=int(len(word) / difficulty), message=None, bot=self.bot)
        await self.up(ctx.message.channel)

    @pendu.command(name="up")
    @debuggable
    async def pendu_up(self, ctx):
        if ctx.message.channel.id not in self.games.keys():
            return await ctx.send("Pas de pendu en cours !")

        await self.up(ctx.channel)

    async def up(self, channel: Channel):
        self.games[channel.id].message = await channel.send("uwu")
        await self.games[channel.id].update()

    @pendu.command(name="leaderboard", aliases=["lb"])
    @debuggable
    async def pendu_lb(self, ctx, subrange: str = None):
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

        out = f"## Leaderboard du pendu\n"
        for rank, user_id, correct_count, total_count, accuracy in leaderboard:
            name = sanitize(self.bot.nickname_cache.get_nick(user_id))
            percentage = round(100.0*accuracy, 2)

            out += f"{rank}. {name} - Précision : {percentage}% ({correct_count}/{total_count} lettres)\n"

        await ctx.send(out)


def setup(bot):
    bot.add_cog(Pendu(bot))
