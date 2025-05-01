from __future__ import annotations

import discord
from discord.ext import commands

import io
import typst
import asyncio

from utils import debuggable

prefix = """
#set page(
  width: 300pt,
  height: auto,
  margin: 5pt,
  fill: none,
)

#set text(
  fill: white,
)
"""

def compile_to_png(source: str) -> io.BytesIO:
    return io.BytesIO(typst.compile(bytes(source, encoding="utf-8"), format="png", ppi=400.0))


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
        
        try:
            loop = asyncio.get_running_loop()
            with ProcessPoolExecutor() as pool:
                rendered = await loop.run_in_executor(pool, compile_to_png, content)

            except RuntimeError as e:
                reason = e.args[0].replace("`", "​`")
                return await ctx.send(f"Error while parsing typst:\n```{reason}```")


            file = discord.File(rendered, "rendered.png")

            await ctx.send(file=file)

            rendered.close()


    def setup(bot):
        bot.add_cog(Typst(bot))
