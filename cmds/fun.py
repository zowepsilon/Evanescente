import discord
from discord.ext import commands
import random

class Fun(commands.Cog): # create a class for our cog that inherits from commands.Cog
    # this class is used to create a cog, which is a module that can be added to the bot

    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot
        self.repeat = True

    @commands.Cog.listener()
    async def on_message(self, message):
        pass

    @commands.command()
    async def roll(self, ctx, *, dices: str = ""):
        rolls = []
        for d in dices.split():
            if d[0] == 'd':
                n = 1
            elif d[0] in '0123456789':
                n = int(d[0])
                d = d[1:]
            else:
                return await ctx.send(f"Dé invalide: {d}")

            if d[0] != 'd':
                return await ctx.send(f"Dé invalide: {d}")

            d = d[1:]

            try:
                m = int(d)
            except ValueError:
                return await ctx.send(f"Dé invalide: {d}")
            
            try:
                for _ in range(n):
                    rolls.append(random.randint(1, m))
            except:
                return await ctx.send(f"Dé invalide: {d}")
        
        if len(rolls) == 0:
            return await ctx.send(f"{ctx.author.mention} choisit le déterminisme...")
        if len(rolls) == 1:
            await ctx.send(f"{ctx.author.mention} a tiré un {rolls[0]}.")
        else:
            rolls = [str(r) for r in rolls]
            await ctx.send(f"{ctx.author.mention} a tiré " + ', '.join(rolls[:-1]) + f"et {rolls[-1]}")

def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Fun(bot)) # add the cog to the bot
