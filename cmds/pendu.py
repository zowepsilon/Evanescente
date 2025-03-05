from __future__ import annotations

import discord
from discord.ext import commands

import asyncio
import random
import sqlite3
from dataclasses import dataclass, field

from utils import debuggable, sanitize, words_of_message

cute = ["uwu", ":3", "rawr", "owo", "catgirl", "bébou"]

insultes = ["chokbar", "putain", "merde", "fuck", "shit", "ptn"]
tokipona = ["toki ", "pona ", "ala ", " li ", "mute ", "wile ", "jan ", "kama ", "waso ", "sina "]

@dataclass
class PenduState:
    message: Message
    word: str
    remaining: int

    found: set[str] = field(default_factory=set)
    wrong: set[str] = field(default_factory=set)

    win: bool = False

    def complete(self) -> bool:
        return all(c in self.found for c in self.word)

    def partial_word(self) -> str:
        return ''.join(c if c in self.found else '_' for c in self.word)

    async def update(self):
        out = ""

        if self.complete():
            out += "## Gagné !\n"
        elif self.remaining == 0:
            out += "## Perdu !\n"

        if self.remaining != 0 and not self.complete():
            out += f"### Le mot est `{self.partial_word()}`."
        else:
            out += f"### Le mot était `{self.word}`."

        out += f"- Coups restants: {self.remaining}"

        out += "- Lettres trouvées : " + ''.join(sorted(list(self.found)))
        out += "- Lettres incorrectes : " + ''.join(sorted(list(self.wrong)))

        await self.message.edit(out)


class Pendu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repeat = True

        self.games: dict[int, PenduState] = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if len(message.content) != 1 or message.author.bot or message.content[0] == '?':
            return

        channel = message.channel.id
        if message.channel.id not in self.games.keys():
            return

        letter = message.content[0]
        word = self.games[channel].word

        if letter in word:
            self.games[channel].found.add(letter)
            await self.games[channel].update()
            await self.games[channel].message.add_reaction("✔️")
            
            if self.games[channel].complete():
                self.games.pop(channel)
        else:
            self.games[channel].wrong.add(letter)
            self.games[channel].remaining -= 1
            await self.games[channel].update()
            await self.games[channel].message.add_reaction("❌")

            if self.games[channel].remaining == 0:
                self.games.pop(channel)

    @commands.group(invoke_without_command=True)
    @debuggable
    async def pendu(self, ctx):
       await ctx.send("Usage: `pendu start`, `pendu ff`")

    @pendu.command(name="start")
    @debuggable
    async def pendu_start(self, ctx, difficulty: float = 0.2):
        word = self.bot.word_counter.get_random_word()
        message = await ctx.send("UwU")
        self.games[ctx.channel.id] = PenduState(word=word, remaining=int(len(word) / difficulty), message=message)
        await self.games[ctx.channel.id].update()

def setup(bot):
    bot.add_cog(Pendu(bot))
