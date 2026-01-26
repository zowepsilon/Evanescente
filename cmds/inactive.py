import discord
from discord.ext import commands

from utils import debuggable, InactiveRolesDb


class Inactive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repeat = True

        self.db = InactiveRolesDb(self.bot.cursor, "InactiveRoles")

    @commands.command()
    @debuggable
    async def make_inactive(self, ctx, member: discord.Member):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You must be an admin to do that!")
            return

        roles = [int(role.id) for role in member.roles[1:]]
        self.db.make_inactive(member.id, roles)

        inactive_role = ctx.guild.get_role(self.bot.config["inactive_role_id"])

        await member.remove_roles(*member.roles[1:], reason="EVA: removed for inactivity")
        await member.add_roles(inactive_role, reason="EVA: added for inactivity")

        await ctx.send("Ce membre est maintenant marqué comme inactif !")

    @commands.command()
    @debuggable
    async def make_active(self, ctx, member: discord.Member):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You must be an admin to do that!")
            return

        roles = self.db.make_active(member.id)
        if roles is None:
            await ctx.send("Ce membre est déjà actif !")
            return

        roles = [ctx.guild.get_role(role_id) for role_id in roles]
        inactive_role = ctx.guild.get_role(self.bot.config["inactive_role_id"])

        await member.add_roles(*roles, reason="EVA: added for activity")
        await member.remove_roles(inactive_role, reason="EVA: removed for activity")

        await ctx.send("Ce membre n'est plus marqué comme inactif !")


    @commands.command()
    @debuggable
    async def check_activity(self, ctx, member: discord.Member):
        date = None
        async for msg in member.history(limit=10):
            await ctx.send(f"{msg.author.display_name} : {msg.content} - {msg.created_at}")
            date = msg.created_at



def setup(bot):
    bot.add_cog(Inactive(bot))
