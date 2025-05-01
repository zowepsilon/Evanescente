from __future__ import annotations

import discord
from discord.ext import commands

import io
import typst

from utils import debuggable

prefix = """
#set page(
  width: 100pt,
  height: auto,
  margin: 5pt,
  fill: none,
)

#set text(
  fill: white,
)
"""


class Typst(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repeat = True

    @commands.command()
    @debuggable
    async def typst(self, ctx, *, content: str = None):
        if content is None:
            if ctx.message.reference is None:
                return await ctx.send("Il faut répondre à un message contenant du code ou donner le code en argument !")

            content = (await ctx.fetch_message(ctx.message.reference.message_id)).content

        source = prefix + content
        
        rendered = io.BytesIO(typst.compile(bytes(source, encoding="utf-8"), format="png", ppi=400.0))
        file = discord.File(rendered, "rendered.png")

        await ctx.send(file=file)

        rendered.close()


def setup(bot):
    bot.add_cog(Typst(bot))
