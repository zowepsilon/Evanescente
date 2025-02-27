import functools
import traceback

def debuggable(f):
    print(f"wrapping {f}")

    @functools.wraps(f)
    async def new(self, ctx, *args, **kwargs):
        try:
            await f(self, ctx, *args, **kwargs)
        except Exception as exc:
            if self.bot.config["debug"] and ctx.author.id == self.bot.config["owner"]:
                await ctx.send(f"Exception lors de l'exécution: ```\n{traceback.format_exc()}```")

    print(f"wrapped {new}")

    return new
