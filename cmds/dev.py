import discord
from discord.ext import commands
from utils import debuggable
from rebuilder import DatabaseRebuilder

import time
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
        if not self.bot.is_dev(ctx.author.id):
            return await ctx.send(":no_entry_sign: You need to be a developer to do that!")
        async with ctx.message.channel.typing():
            with open(self.bot.CONFIG_PATH, mode='r') as f:
                self.bot.config = json.load(f)
        await ctx.send(":white_check_mark: Reloaded configuration!")

    @config.command(name="save")
    @debuggable
    async def config_save(self, ctx):
        if not self.bot.is_dev(ctx.author.id):
            return await ctx.send(":no_entry_sign: You need to be a developer to do that!")
        async with ctx.message.channel.typing():
            with open(self.bot.CONFIG_PATH, mode='w') as f:
                json.dump(self.bot.config, f, indent=4)
        await ctx.send(":white_check_mark: Saved configuration!")

    @commands.group(invoke_without_command=True)
    @debuggable
    async def ext(self, ctx):
        await ctx.send("You must provide a subcommand (`reload` or `add`)")

    @ext.command(name="reload")
    @debuggable
    async def ext_reload(self, ctx, extension: str = None):
        if not self.bot.is_dev(ctx.author.id):
            return await ctx.send("You need to be a developer to do that!")

        self.bot.reload_time = time.gmtime()
        if extension is None:
            for ext in list(self.bot.extensions.keys()):
                try:
                    self.bot.reload_extension(ext)
                except Exception as err:
                    return await ctx.send(f"An error occured while trying to load `{ext}`.\n`{err.__class__.__name__}: {err}`")
            return await ctx.send(f"Successfully reloaded all extensions !")
        try:
            self.bot.reload_extension(extension)
        except Exception as err:
            return await ctx.send(f":no_entry_sign: An error occured while trying to load `{extension}`.\n`{err.__class__.__name__}: {err}`")
        await ctx.send(f"Successfully reloaded `{extension}` !")

    @ext.command(name="add")
    @debuggable
    async def ext_add(self, ctx, extension: str):
        if not self.bot.is_dev(ctx.author.id):
            return await ctx.send("You need to be a developer to do that!")
        try:
            self.bot.load_extension(extension)
            self.bot.loaded_extensions.append(extension)
        except Exception as err:
            return await ctx.send(f":no_entry_sign: An error occured while trying to load `{extension}`.\n`{err.__class__.__name__}: {err}`")
        await ctx.send(f":white_check_mark: Successfully added `{extension}` !")

    @commands.command()
    @debuggable
    async def rebuild(self, ctx):
        if not self.bot.is_dev(ctx.author.id):
            return await ctx.send("You need to be a developer to do that!")

        self.bot.reload_time = time.gmtime()

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
    async def reload_names(self, ctx):
        if not self.bot.is_dev(ctx.author.id):
            return await ctx.send("You need to be a developer to do that!")
        async with ctx.message.channel.typing():
            for m in ctx.author.guild.members:
                self.bot.nickname_cache.set_nick(m.id, m.display_name)

            await ctx.send(f"Les noms de {len(ctx.author.guild.members)} membres ont été rechargés !")

    @commands.command()
    @debuggable
    async def sql(self, ctx, *, request: str):
        if not self.bot.is_dev(ctx.author.id):
            return await ctx.send("You need to be a developer to do that!")

        request = request.split()

        if request[0].lower() == "drop" and request[1].lower() == "table":
            return await ctx.send(f"Dropped table {request[2]} !")

    @commands.command()
    @debuggable
    async def debug(self, ctx):
        if not self.bot.is_dev(ctx.author.id):
            return await ctx.send("You need to be a developer to do that!")

        self.bot.config["debug"] = not self.bot.config["debug"]
        await ctx.send(f"Le mode debug a été " + ("activé !" if self.bot.config["debug"] else "désactivé !"))

    @commands.command()
    @debuggable
    async def blacklist(self, ctx):
        if not self.bot.is_dev(ctx.author.id):
            return await ctx.send("You need to be a developer to do that!")

        channel = ctx.channel.id

        if channel in self.bot.config["blacklist"]:
            self.bot.config["blacklist"].remove(channel)
            await ctx.send(f"{ctx.channel.mention} a été retiré de la blacklist.")
        else:
            self.bot.config["blacklist"].append(channel)
            await ctx.send(f"{ctx.channel.mention} a été ajouté de la blacklist.")


    @commands.command()
    @debuggable
    async def rebuild_every_part_of_the_database(self, ctx, db_path: str):
        if not self.bot.is_dev(ctx.author.id):
            return await ctx.send("You need to be a developer to do that!")
        
        rebuilder = DatabaseRebuilder(db_path)
        await ctx.send(f"DB connectée à {db_path}")

        all_messages = []
        ui
        n = 0
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.CategoryChannel):
                continue

            n += 1

            try:
                channel_messages = await channel.history(limit=None).flatten()
            except discord.Forbidden:
                continue

            await ctx.send(f"- {len(channel_messages)} trouvés dans {channel.name}")
            all_messages.extend(channel_messages)

        await ctx.send(f"{n} salons ont été analysés pour {len(all_messages)} messages au total.\nJe trie les messages par date...")
        all_messages.sort(key=lambda message: message.created_at)
        await ctx.send(f"Tri des messages terminé !")
        await ctx.send(f"Début du traitement des messages...")
        for i, message in enumerate(all_messages):
            if i % 5000 == 0:
                await ctx.send(f"{i} messages ont été traités")

            rebuilder.process_message(message)

        await ctx.send("Les messages ont bien été traités !")
        await ctx.send("Début du caching des noms...")
        
        for m in ctx.author.guild.members:
            self.bot.nickname_cache.set_nick(m.id, m.display_name)

        await ctx.send(f"Les noms de {len(ctx.author.guild.members)} membres ont été rechargés !")
        

def setup(bot): 
    bot.add_cog(Developper(bot))
