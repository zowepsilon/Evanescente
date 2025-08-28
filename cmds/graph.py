import discord
from discord.ext import commands

import io
import graphviz

from utils import debuggable, sanitize, GraphDb

class Graph(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repeat = True

        self.db = GraphDb(self.bot.cursor, "MeetingGraph")

    @commands.group(invoke_without_command=True)
    @debuggable
    async def graph(self, ctx):
        rendered = self.render()

        file = discord.File(rendered, filename="graph.png")
        await ctx.send(file=file)
        
    def render(self) -> bytes:
        edges = self.db.get_graph()
        nodes = {e[0] for e in edges} | {e[1] for e in edges}
        
        g = graphviz.Graph(engine='neato', format='png')

        for uid in nodes:
            g.node(str(uid), self.bot.get_nick(uid))

        for (u, v) in edges:
            g.edge(str(u), str(v))

        return g.pipe()

    @debuggable
    async def _graph(self, ctx, target: discord.Member = None, level: int = None):
        if target is None or level is None:
            target = ctx.author.id if target is None else target.id
            
            name = sanitize(self.bot.nickname_cache.get_nick(target))

            try:
                level, votes = self.db.get_sanity(target)
                level = round(level)
            except ZeroDivisionError:
                return await ctx.send(f"{name} n'a pas encore de taux de santé mentale !")

            return await ctx.send(f"Taux de santé mentale de {name} : {level}% ({votes} estimations)")

        if target.id == ctx.author.id:
            return await ctx.send("Tu ne peux pas estimer ton propre taux de santé mentale.")
        
        if level < 0 or level > 100:
            return await ctx.send("Le taux de santé mentale doit être compris entre 0 et 100.")

        self.db.change_entry(target.id, ctx.author.id, level)

        name = sanitize(self.bot.nickname_cache.get_nick(target.id))
        new_level, votes = self.db.get_sanity(target.id)
        new_level = round(new_level)

        await ctx.send(f"Tu as estimé le taux de santé mentale de {name} à {level}%.\nTaux de santé mentale : {new_level}% ({votes} estimations)")


def setup(bot):
    bot.add_cog(Graph(bot))
