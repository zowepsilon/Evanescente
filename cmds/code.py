from __future__ import annotations

import discord
from discord.ext import commands

from dataclasses import dataclass

import json
import time
import asyncio
from websockets.asyncio.client import connect

from utils import debuggable

@dataclass
class RunnerState:
    stdout: str
    stderr: str
    finished: bool

    message: Message

    async def update_message(self):
        out = "Exécution en cours...\n" if not self.finished else "Exécution terminée\n"

        if self.stderr != "":
            out += "-# STDERR\n"
            out += "```rust\n"
            out += self.stderr.replace("`", "​`")
            out += "```\n"

        if self.stdout != "":
            out += "-# STDOUT\n"
            out += "```\n"
            out += self.stdout.replace("`", "​`")
            out += "```\n"

        await self.message.edit(out)


class Code(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repeat = True

    @commands.command()
    @debuggable
    async def run(self, ctx, *, code: str = None):
        if code is None:
            if ctx.message.reference is None:
                return await ctx.send("Il faut répondre à un message contenant du code ou donner le code en argument !")

            code = (await ctx.fetch_message(ctx.message.reference.message_id)).content


        if code.startswith("```rust"):
            code = code[7:-3]
        elif code.startswith("```"):
            code = code[3:-3]
    
        if "fn main()" not in code:
            code = f"""
            fn main() {{
                {code}
            }}
            """

        code = code.replace("\n", "\\n").replace("\"", "\\\"")

        TIMEOUT = 10

        async with connect("wss://play.rust-lang.org/websocket") as websocket:
            message = await ctx.send("Exécution en cours...")
            state = RunnerState(stdout="", stderr="", finished=False, message=message)

            await websocket.send('{"type":"websocket/connected","payload":{"iAcceptThisIsAnUnsupportedApi":true},"meta":{"websocket":true,"sequenceNumber":0}}')
            await websocket.recv()
            await websocket.recv()

            req = '{"type":"output/execute/wsExecuteRequest","payload":{"channel":"nightly","mode":"debug","edition":"2024","crateType":"bin","tests":false,"code":"' \
                + code \
                + '","backtrace":false},"meta":{"websocket":true,"sequenceNumber":1}}'
            await websocket.send(req)

            start = time.time()

            async for message in websocket:
                res = json.loads(message)


                match res["type"]:
                    case "output/execute/wsExecuteEnd":
                        state.finished = True
                        await state.update_message()
                        break

                    case "output/execute/wsExecuteStderr":
                        state.stderr += res["payload"]
                        await state.update_message()

                    case "output/execute/wsExecuteStdout":
                        state.stdout += res["payload"]
                        await state.update_message()
                    

                if time.time() > start + TIMEOUT:
                    state.finished = True
                    await state.update_message()
                    break

def setup(bot):
    bot.add_cog(Code(bot))
