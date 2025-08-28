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

    def render(self) -> graphviz.Graph:
        edges = self.db.get_graph()
        nodes = {e[0] for e in edges} | {e[1] for e in edges}
        
        g = graphviz.Graph(engine='neato', format='png')
        #g = graphviz.Graph(format='png')

        for uid in nodes:
            g.node(str(uid), self.bot.nickname_cache.get_nick(uid))

        for (u, v) in edges:
            g.edge(str(u), str(v))

        return g

    @commands.group(invoke_without_command=True)
    @debuggable
    async def graph(self, ctx):
        rendered = io.BytesIO(self.render().pipe())

        file = discord.File(rendered, filename="graph.png")
        await ctx.send(file=file)

        rendered.close()

    @graph.command(name='add')
    @debuggable
    async def graph_add(self, ctx, other: discord.Member):
        if target.id == ctx.author.id:
            await ctx.send("Tu ne peux pas ajouter d'arête triviale.")
            return

        user1_nick = sanitize(self.bot.nickname_cache.get_nick(ctx.author.id))
        user2_nick = sanitize(self.bot.nickname_cache.get_nick(other.id))

        if self.db.get_edge(ctx.author.id, other.id):
            await ctx.send(f"L'arête entre {user1_nick} et {user2_nick} existe déjà !")
        else:
            self.db.add_edge(ctx.author.id, other.id)
            await ctx.send(f"L'arête entre {user1_nick} et {user2_nick} a été ajoutée !")

    @graph.command(name="source")
    async def graph_source(self, ctx):
        source = io.StringIO(self.render().source)

        file = discord.File(source, filename="graph.gv")
        await ctx.send(file=file)

        source.close()

def setup(bot):
    bot.add_cog(Graph(bot))
