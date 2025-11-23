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
        if not self.db.make_inactive(member.id, roles):
            await ctx.send("Ce membre est déjà inactif !")
            return

        inactive_role = await ctx.guild.get_role(self.bot.config["inactive_role_id"])

        self.remove_roles(*member.roles[1:], reason="EVA: removed for inactivity")
        self.add_roles(inactive_role, reason="EVA: added for inactivity")

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

        self.add_roles(*roles, reason="EVA: added for activity")
        self.remove_roles(inactive_role, reason="EVA: removed for activity")


def setup(bot):
    bot.add_cog(Inactive(bot))
