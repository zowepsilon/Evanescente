import random
from time import strftime

import discord
from discord.ext import commands

import aiohttp

from utils import debuggable, sanitize


class Miscellaneous(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.repeat = True
        
        with open(self.bot.SOURCE + "/lgd.txt") as f:
            self.quotes = []
            for line in f.readlines():
                line = line[:-1]
                i, h, text = line.split('|')
                self.quotes.append((i, h, text))

    @commands.Cog.listener()
    async def on_ready(self):
        

        print(f"Bot ready, logged in as {self.bot.user}.")

    @commands.command()
    @debuggable
    async def ping(self, ctx):
        await ctx.send(f"<:bonk:1363133543726845952> in {round(self.bot.latency*1000)}ms!")

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
    async def abitbol(self, ctx, *, index: str = None):
        if index is None:
            i, h, quote =  random.choice(self.quotes)
            return await ctx.send(f"\"{quote}\"\nhttp://george-abitbol.fr/doc/mp4/{i}.mp4\n-# #{i}/{len(self.quotes)+1}")

        try:
            matches = [int(index)]
        except ValueError:
            matches = [int(i) for (i, h, quote) in self.quotes if index.lower() in quote.lower()]


        if len(matches) == 0:
            await ctx.send("Aucun extrait trouvé !")
        elif len(matches) == 1:
            i, h, quote = self.quotes[matches[0]-1]

            await ctx.send(f"\"{quote}\"\nhttp://george-abitbol.fr/doc/mp4/{i}.mp4\n-# #{i}/{len(self.quotes)+1}")
        else:
            i, h, quote = self.quotes[matches[0]-1]

            others = "-# Autres extraits : "
            for m in matches[1:-1]:
                others += f"#{m}, "

            others += f"#{matches[-1]}"

            await ctx.send(f"\"{quote}\"\nhttp://george-abitbol.fr/doc/mp4/{i}.mp4\n-# #{i}/{len(self.quotes)+1}\n{others}")

    @commands.command()
    @debuggable
    async def xkcd(self, ctx, *, search: str):
        # curl '' --compressed -X POST --data-raw '' | py -m json.tool
        url = "https://qtg5aekc2iosjh93p.a1.typesense.net/multi_search?use_cache=true&x-typesense-api-key=8hLCPSQTYcBuK29zY5q6Xhin7ONxHy99"
        search = search.replace('\"', "\\\"")
        data = f'''{{
            "searches":[{{
                "query_by":"title,altTitle,transcript,topics,embedding",
                "query_by_weights":"127,80,80,1,1",
                "num_typos":1,
                "exclude_fields":"embedding",
                "vector_query":"embedding:([], k: 30, distance_threshold: 0.1, alpha: 0.9)",
                "highlight_full_fields":"title,altTitle,transcript,topics,embedding",
                "collection":"xkcd",
                "q":"{search}",
                "facet_by":"publishDateYear,topics",
                "max_facet_values":100,
                "page":1,
                "per_page":1
            }}]
        }}'''

        async with self.bot.session.post(url, data=data) as req:
            doc = (await req.json())["results"][0]["hits"][0]["document"]
            index, title, url, alt = doc["id"], doc["title"], doc["imageUrl"], doc["altTitle"]


        await ctx.send(f"\"**{title}**\"\n-# {alt}\n-# [#{index}]({url})")


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
            "o": (
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
                for char in msg_line:
                    out += art[char][line].translate(trans) + "      "
                
                out += "\n"
            out += "\n"

        await ctx.send(out)


def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Miscellaneous(bot)) # add the cog to the bot
