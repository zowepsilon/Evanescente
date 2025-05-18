import discord
from discord.ext import commands

import io
import asyncio
import random
import sqlite3

from utils import debuggable, sanitize, SanityDb

class Sanity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repeat = True

        self.db = SanityDb(self.bot.cursor, "Sanities")

    @commands.command()
    @debuggable
    async def sanity(self, ctx, target: discord.Member = None, level: int = None):
        if target is None or level is None:
            target = ctx.author.id if target is None else target.id
            
            name = sanitize(self.bot.nickname_cache.get_nick(target))

            try:
                level = self.db.get_sanity(target)
            except ZeroDivisionError:
                return await ctx.send(f"{name} n'a pas encore de taux de santé mentale !")

            return await ctx.send(f"Taux de santé mentale de {name} : {level}%")

        if target.id == ctx.author.id:
            return await ctx.send("Tu ne peux pas estimer ton propre taux de santé mentale.")
        
        if level < 0 or level > 100:
            return await ctx.send("Le taux de santé mentale doit être compris entre 0 et 100.")

        self.db.change_entry(target.id, ctx.author.id, level)

        name = sanitize(self.bot.nickname_cache.get_nick(target.id))
        new_level = self.db.get_sanity(target.id)

        await ctx.send(f"Tu as estimé le taux de santé mentale de {name} à {level}%.\nTaux de santé mentale : {new_level}%")


def setup(bot):
    bot.add_cog(Sanity(bot))
