import discord
from discord.ext import commands
from utils import debuggable, sanitize

from time import strftime

class Miscellaneous(commands.Cog): # create a class for our cog that inherits from commands.Cog
    # this class is used to create a cog, which is a module that can be added to the bot

    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot
        self.repeat = True

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Bot ready, logged in as {self.bot.user}")

    @commands.command()
    @debuggable
    async def ping(self, ctx):
        await ctx.send(f"Bonk in {round(self.bot.latency*1000)}ms!")

    @commands.command()
    @debuggable
    async def about(self, ctx):
        startup = strftime("%d/%m/%Y à %H:%M:%S", self.bot.startup_time)
        reload = strftime("%d/%m/%Y à %H:%M:%S", self.bot.reload_time)

        await ctx.send(f"{self.bot.user.name} - she/her - Faite par Zoé, lancée le {startup}, rechargée le {reload}.")

    @commands.command()
    @debuggable
    async def fuck(self, ctx, *, target: str = "you"):
        if "you" in target:
            return await ctx.send("no u")
        else:
            target = sanitize(target)
            return await ctx.send(f"Fucked {target}! :+1:")

    @commands.command()
    @debuggable
    async def rickroll(self, ctx):
        await ctx.send("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    @commands.command()
    @debuggable
    async def roll(self, ctx, *, dices: str = ""):
        rolls = []
        for raw_d in dices.split():
            d = raw_d

            if d[0] == 'd':
                n = 1
            elif d[0] in '0123456789':
                n = int(d[0])
                d = d[1:]
            else:
                return await ctx.send(f"Dé invalide: {raw_d}")

            if d[0] != 'd':
                return await ctx.send(f"Dé invalide: {raw_d}")

            d = d[1:]

            try:
                m = int(d)
            except ValueError:
                return await ctx.send(f"Dé invalide: {raw_d}")
            
            try:
                for _ in range(n):
                    rolls.append(random.randint(1, m))
            except:
                return await ctx.send(f"Dé invalide: {raw_d}")
        
        if len(rolls) == 0:
            return await ctx.send(f"{ctx.author.mention} choisit le déterminisme...")
        if len(rolls) == 1:
            await ctx.send(f"{ctx.author.mention} a tiré un {rolls[0]}.")
        else:
            rolls = [str(r) for r in rolls]
            await ctx.send(f"{ctx.author.mention} a tiré " + ', '.join(rolls[:-1]) + f" et {rolls[-1]}.")

    @commands.command()
    @debuggable
    async def blood(self, ctx, *, message: str):
        art = {
            "a": (
                "#####",
                "#   #",
                "#####",
                "#   #",
                "#   #",
            ),
            "b": (
                "#### ",
                "#   #",
                "#### ",
                "#   #",
                "#### ",
            ),
            "c": (
                "#####",
                "#    ",
                "#    ",
                "#    ",
                "#####",
            ),
            "d": (
                "#### ",
                "#   #",
                "#   #",
                "#   #",
                "#### ",
            ),
            "e": (
                "#####",
                "#    ",
                "#### ",
                "#    ",
                "#####",
            ),
            "f": (
                "#####",
                "#    ",
                "#### ",
                "#    ",
                "#    ",
            ),
            "g": (
                "#####",
                "#    ",
                "#  ##",
                "#   #",
                "#####",
            ),
            "h": (
                "#   #",
                "#   #",
                "#####",
                "#   #",
                "#   #",
            ),
            "i": (
                "###",
                " # ",
                " # ",
                " # ",
                "###",
            ),
            "j": (
                "   #",
                "   #",
                "   #",
                "#  #",
                " ## ",
            ),
            "k": (
                "#  ##",
                "# ## ",
                "###  ",
                "# ## ",
                "#  ##",
            ),
            "l": (
                "#    ",
                "#    ",
                "#    ",
                "#    ",
                "#####",
            ),
            "m": (
                "### ###",
                "#  #  #",
                "#  #  #",
                "#  #  #",
                "#  #  #",
            ),
            "n": (
                "#   #",
                "##  #",
                "# # #",
                "#  ##",
                "#   #",
            ),
            "block": (
                "#####",
                "#   #",
                "#   #",
                "#   #",
                "#####",
            ),
            "p": (
                "#### ",
                "#   #",
                "#### ",
                "#    ",
                "#    ",
            ),
            "q": (
                "#####",
                "#   #",
                "# # #",
                "#  # ",
                "### #",
            ),
            "r": (
                "#### ",
                "#   #",
                "#### ",
                "# #  ",
                "#  # ",
            ),
            "s": (
                "#####",
                "#    ",
                "#####",
                "    #",
                "#####",
            ),
            "t": (
                "#####",
                "  #  ",
                "  #  ",
                "  #  ",
                "  #  ",
            ),
            "u": (
                "#   #",
                "#   #",
                "#   #",
                "#   #",
                " ### ",
            ),
            "v": (
                "#   #",
                "#   #",
                " # # ",
                " # # ",
                "  #  ",
            ),
            "w": (
                "#   #   #",
                "#   #   #",
                " # # # # ",
                " # # # # ",
                "  #   #  ",
            ),
            "x": (
                "#   #",
                " # # ",
                "  #  ",
                " # # ",
                "#   #",
            ),
            "y": (
                "#   #",
                "#   #",
                " ####",
                "    #",
                " ####",
            ),
            "z": (
                "#####",
                "   # ",
                "  #  ",
                " #   ",
                "#####",
            ),
            " ": (
                "     ",
                "     ",
                "     ",
                "     ",
                "     ",
            ),
            "(": (
                " #",
                "# ",
                "# ",
                "# ",
                " #",
            ),
            ")": (
                "# ",
                " #",
                " #",
                " #",
                "# ",
            ),
            "{": (
                " #",
                "# ",
                " #",
                "# ",
                " #",
            ),
            "}": (
                "# ",
                " #",
                "# ",
                " #",
                "# ",
            ),
            "block": (
                "#####",
                "#####",
                "#####",
                "#####",
                "#####",
            ),
        }
        trans = str.maketrans({"#": ":drop_of_blood:", " ": "      "})

        message = message.lower()
        
        out = ""
        for msg_line in message.splitlines():
            out += "​"
            for line in range(5):
                for char in message:
                    out += art[char][line].translate(trans) + "      "
                
                out += "\n"
            out += "\n"

        await ctx.send(out)


def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Miscellaneous(bot)) # add the cog to the bot
