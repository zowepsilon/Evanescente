from __future__ import annotations

import discord
from discord.ext import commands

import io
import typst
import asyncio
import concurrent.futures

from utils import debuggable

prefix = """
#set page(
  height: auto,
  margin: 5pt,
  fill: none,
)

#set page(width: 300pt) // if #page.width > 300pt

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

        self.renders: dict[int, discord.Message] = {}

    async def process(self, ctx, message_id: int, content: str):
        if message_id in self.renders.keys():
            await self.renders[message_id].delete()

        source = prefix + content
        
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ProcessPoolExecutor() as pool:
                rendered = await loop.run_in_executor(pool, compile_to_png, source)
            
        except RuntimeError as e:
            reason = e.args[0].replace("`", "​`")
            self.renders[message_id] = await ctx.send(f"Error while parsing typst:\n```{reason}```")
            return

        file = discord.File(rendered, "rendered.png")
        self.renders[message_id] = await ctx.send(file=file)
        rendered.close()

    @commands.command()
    @debuggable
    async def typst(self, ctx, *, content: str = None):
        if content is None:
            if ctx.message.reference is None:
                return await ctx.send("Il faut répondre à un message contenant du code ou donner le code en argument !")

            content = (await ctx.fetch_message(ctx.message.reference.message_id)).content
            await self.process(ctx, ctx.message.reference.message_id, content)
        else:
            await self.process(ctx, ctx.message.id, content)


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or len(message.content) == 0 or message.content[0] == '?':
            return
        
        if message.content.count('$') >= 2:
            await self.process(message.channel, message.id, message.content)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

        if message.author.bot or len(message.content) == 0 or message.content[0] == '?':
            return
        
        if message.content.count('$') >= 2:
            await self.process(message.channel, message.id, message.content)
        
def setup(bot):
    bot.add_cog(Typst(bot))
