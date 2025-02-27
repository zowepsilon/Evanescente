import discord
from discord.ext import commands
from utils import debuggable

import json
import subprocess

class Developper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @debuggable
    async def config(self, ctx):
        await ctx.send(":no_entry_sign: You must provide a subcommand (`save` or `reload`)")

    @config.command(name="reload")
    @debuggable
    async def config_reload(self, ctx):
        if not await self.bot.is_owner(ctx.author):
            return await ctx.send(":no_entry_sign: You need to be the owner to do that!")
        async with ctx.message.channel.typing():
            with open(self.bot.CONFIG_PATH, mode='r') as f:
                self.bot.config = json.load(f)
        await ctx.send(":white_check_mark: Reloaded configuration!")

    @config.command(name="save")
    @debuggable
    async def config_save(self, ctx):
        if not await self.bot.is_owner(ctx.author):
            return await ctx.send(":no_entry_sign: You need to be a moderator to do that!")
        async with ctx.message.channel.typing():
            with open(self.bot.CONFIG_PATH, mode='w') as f:
                json.dump(self.bot.config, f, indent=4)
        await ctx.send(":white_check_mark: Saved configuration!")

    @commands.group(invoke_without_command=True)
    @debuggable
    async def ext(self, ctx):
        await ctx.send(":no_entry_sign: You must provide a subcommand (`reload` or `add`)")

    @ext.command(name="reload")
    @debuggable
    async def ext_reload(self, ctx, extension: str = None):
        print(await self.bot.is_owner(ctx.author))
        if not await self.bot.is_owner(ctx.author):
            return await ctx.send(":no_entry_sign: You need to be the owner to do that!")
        if extension is None:
            for ext in list(self.bot.extensions.keys()):
                try:
                    self.bot.reload_extension(ext)
                except Exception as err:
                    return await ctx.send(f":no_entry_sign: An error occured while trying to load `{ext}`.\n`{err.__class__.__name__}: {err}`")
            return await ctx.send(f":white_check_mark: Successfully reloaded all extensions !")
        try:
            self.bot.reload_extension(extension)
        except Exception as err:
            return await ctx.send(f":no_entry_sign: An error occured while trying to load `{extension}`.\n`{err.__class__.__name__}: {err}`")
        await ctx.send(f"Successfully reloaded `{extension}` !")

    @ext.command(name="add")
    @debuggable
    async def ext_add(self, ctx, extension: str):
        if not await self.bot.is_owner(ctx.author):
            return await ctx.send(":no_entry_sign: You need to be the owner to do that!")
        try:
            self.bot.load_extension(extension)
            self.bot.loaded_extensions.append(extension)
        except Exception as err:
            return await ctx.send(f":no_entry_sign: An error occured while trying to load `{extension}`.\n`{err.__class__.__name__}: {err}`")
        await ctx.send(f":white_check_mark: Successfully added `{extension}` !")

    @commands.command()
    @debuggable
    async def rebuild(self, ctx):
        if not await self.bot.is_owner(ctx.author):
            return await ctx.send(":no_entry_sign: You need to be the owner to do that!")
        async with ctx.message.channel.typing():
            output = subprocess.check_output(["git", "pull"]).decode("utf-8")
            await ctx.send(f"```\n{output}```")

            for ext in list(self.bot.extensions.keys()):
                try:
                    self.bot.reload_extension(ext)
                except Exception as err:
                    return await ctx.send(f":no_entry_sign: An error occured while trying to load `{ext}`.\n`{err.__class__.__name__}: {err}`")
            return await ctx.send(f":white_check_mark: Successfully reloaded all extensions !")

        await ctx.send(":white_check_mark: Rebuilt bot!")

    @commands.command()
    @debuggable
    async def exception(self, ctx):
        raise ValueError("user failed")

    @commands.command()
    @debuggable
    async def debug(self, ctx):
        if not await self.bot.is_owner(ctx.author):
            return await ctx.send(":no_entry_sign: You need to be the owner to do that!")

        self.bot.config["debug"] = not self.bot.config["debug"]
        await ctx.send(f"Le mode debug a été " + ("activé !" if self.bot.config["debug"] else "désactivé !"))

def setup(bot): 
    bot.add_cog(Developper(bot))
