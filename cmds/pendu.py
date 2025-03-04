import discord
from discord.ext import commands

import asyncio
import random
import sqlite3
from dataclasses import dataclass, field

from utils import debuggable, sanitize, words_of_message

cute = ["uwu", ":3", "rawr", "owo", "catgirl", "bébou"]

insultes = ["chokbar", "putain", "merde", "fuck", "shit", "ptn"]
tokipona = ["toki ", "pona ", "ala ", " li ", "mute ", "wile", "jan ", "kama ", "waso ", "sina "]

@dataclass
class PenduState:
    word: str
    found: set[str]
    remaining: int

    def complete(self) -> bool:
        return all(c in self.found for c in self.word)

    def partial_word(self) -> str:
        return ''.join(c if c in self.found else '_' for c in self.word)

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

        if letter in self.games[channel].found:
            await self.print_state(message.channel, f"`{letter}` a déjà été trouvée !")
            return

        if letter in word:
            self.games[channel].found.add(letter)
            
            if self.games[channel].complete():
                try:
                    (_, count, user_id) = self.bot.word_counter.get_word_rank(word)
                    nickname =  self.bot.nickname_cache.get_nick(user_id)

                    if nickname is None:
                        nickname = "Inconnu au bataillon"

                    await message.channel.send(f"Gagné ! Le mot était `{word}`, trouvé par @{nickname} et utilisé {count} fois.")
                except TypeError:
                    await message.channel.send(f"Gagné ! Le mot était `{word}`. Ses statistiques sont inconnues.")
                self.games.pop(channel)
            else:
                await self.print_state(message.channel, f"`{letter}` était dans le mot !")
        else:
            self.games[channel].remaining -= 1

            if self.games[channel].remaining == 0:
                await message.channel.send(f"Perdu ! Le mot était `{word}`.")
                self.games.pop(channel)
            else:
                await self.print_state(message.channel, f"`{letter}` n'était dans le mot :(")

    async def print_state(self, channel, message = ""):
        state = self.games[channel.id]

        out = f"Le mot est **`{state.partial_word()}`**, vous avez {state.remaining} coups restants"

        await channel.send(f"{message}\n{out}")

    @commands.group(invoke_without_command=True)
    @debuggable
    async def pendu(self, ctx):
       await ctx.send("Usage: `pendu start`, `pendu ff`")

    @pendu.command(name="start")
    @debuggable
    async def pendu_start(self, ctx, difficulty: float = 0.2):
        word = self.bot.word_counter.get_random_word()
        self.games[ctx.channel.id] = PenduState(word=word, found=set(), remaining=int(len(word) / difficulty))
        
        await self.print_state(ctx.channel, "Le pendu a commencé :tada:")


def setup(bot):
    bot.add_cog(Pendu(bot))
