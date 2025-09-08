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

    def render(self, *, center: int  = None) -> graphviz.Graph:
        if center is None:
            edges = self.db.get_graph()
        else:
            edges = self.db.get_adjacent(center)

        nodes = {e[0] for e in edges} | {e[1] for e in edges}

        if center is not None:
            # If `center` hasn't met anyone, then let them feel the weight of their own loneliness.
            nodes.add(center)
        
        if center is None:
            g = graphviz.Graph(format='png')
        else:
            g = graphviz.Graph(format='png', engine='twopi', graph_attr={'root': str(center), "overlap": "false"})

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

    async def add(self, ctx, user1: discord.Member, user2: discord.Member):
        if user1.id == user2.id:
            await ctx.send("Tu ne peux pas ajouter d'arête triviale.")
            return

        user1_nick = sanitize(self.bot.nickname_cache.get_nick(user1.id))
        user2_nick = sanitize(self.bot.nickname_cache.get_nick(user2.id))

        if self.db.get_edge(user1.id, user2.id):
            await ctx.send(f"L'arête entre {user1_nick} et {user2_nick} existe déjà !")
        else:
            self.db.add_edge(user1.id, user2.id)
            await ctx.send(f"L'arête entre {user1_nick} et {user2_nick} a été ajoutée !")

    async def remove(self, ctx, user1: discord.Member, user2: discord.Member):
        if user1.id == user2.id:
            await ctx.send("Tu ne peux pas enlever d'arête triviale.")
            return

        user1_nick = sanitize(self.bot.nickname_cache.get_nick(user1.id))
        user2_nick = sanitize(self.bot.nickname_cache.get_nick(user2.id))

        if self.db.get_edge(user1.id, user2.id):
            self.db.remove_edge(user1.id, user2.id)
            await ctx.send(f"L'arête entre {user1_nick} et {user2_nick} a été supprimée !")
        else:
            await ctx.send(f"L'arête entre {user1_nick} et {user2_nick} n'existe pas !")

    @graph.command(name='add')
    @debuggable
    async def graph_add(self, ctx, other: discord.Member):
        await self.add(ctx, ctx.author, other)

    @graph.command(name='remove')
    @debuggable
    async def graph_remove(self, ctx, other: discord.Member):
        await self.remove(ctx, ctx.author, other)

    @graph.command(name='forceadd')
    @debuggable
    async def graph_forceadd(self, ctx, user1: discord.Member, user2: discord.Member):
        if not self.bot.is_dev(ctx.author.id):
            await ctx.send("Tu n'es pas développeuse !")
            return
        
        await self.add(ctx, user1, user2)

    @graph.command(name='forceremove')
    @debuggable
    async def graph_forceremove(self, ctx, user1: discord.Member, user2: discord.Member):
        if not self.bot.is_dev(ctx.author.id):
            await ctx.send("Tu n'es pas développeuse !")
            return
        
        await self.remove(ctx, user1, user2)
    
    @graph.command(name="source")
    @debuggable
    async def graph_source(self, ctx):
        source = io.StringIO(self.render().source)

        file = discord.File(source, filename="graph.gv")
        await ctx.send(file=file)

        source.close()

    @graph.command(name="local")
    @debuggable
    async def graph_local(self, ctx, *, user: discord.Member = None):
        user = user or ctx.author

        rendered = io.BytesIO(self.render(center=user.id).pipe())

        file = discord.File(rendered, filename="graph.png")
        await ctx.send(file=file)

        rendered.close()

    @graph.command(name="leaderboard", aliases=["lb"])
    @debuggable
    async def graph_lb(self, ctx, subrange: str = None):
        if subrange is not None:
            subrange_spl = subrange.split("-")
            if len(subrange_spl) != 2:
                return await ctx.send(f"Range invalide `{subrange}`. Exemple de range : 5-15")
            try:
                start, end = int(subrange_spl[0]), int(subrange_spl[1])
            except ValueError:
                return await ctx.send(f"Range invalide `{subrange}`. Exemple de range : 5-15")
        
            leaderboard = self.db.get_leaderboard(start, end)
            start -= 1
        else:
            start = None
            end = 10

        leaderboard = self.db.get_leaderboard()[start:end]

        out = "## Leaderboard du graphe\n"
        for i, (user_id, degree) in enumerate(leaderboard):
            name = sanitize(self.bot.nickname_cache.get_nick(user_id))
            out += f"{i+1}. {name} - {degree} personnes rencontrées\n"

        await ctx.send(out)

def setup(bot):
    bot.add_cog(Graph(bot))
