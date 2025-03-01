import discord
from discord.ext import commands
from utils import debuggable

class Miscellaneous(commands.Cog): # create a class for our cog that inherits from commands.Cog
    # this class is used to create a cog, which is a module that can be added to the bot

    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot
        self.repeat = True

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Bot ready, logged in as {self.bot.user}")

    @commands.Cog.listener()
    async def on_message(self, message):
        pass

    @commands.command()
    @debuggable
    async def ping(self, ctx):
        await ctx.send(f"Bonk in {round(self.bot.latency*1000)}ms!")

    @commands.command()
    @debuggable
    async def about(self, ctx):
        owner = await self.bot.fetch_user(self.bot.config["owner"])
        await ctx.send(f"`{self.bot.user.name} v{self.bot.__version__}` - she/her - Made by Zoé")

    @commands.command()
    @debuggable
    async def fuck(self, ctx, *, target: str = "you"):
        if "you" in target:
            return await ctx.send("no u")
        else:
            target = target.replace("@here", "@​here")
            target = target.replace("@everyone", "@​everyone")
            target = target.replace("<@&", "<​@​&​")
            return await ctx.send(f"Fucked {target}! :+1:")

    @commands.command()
    @debuggable
    async def rickroll(self, ctx):
        await ctx.send("https://www.youtube.com/watch?v=dQw4w9WgXcQ")



def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Miscellaneous(bot)) # add the cog to the bot
