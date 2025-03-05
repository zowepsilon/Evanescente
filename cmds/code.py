from __future__ import annotations

import discord
from discord.ext import commands

from dataclasses import dataclass

import json
import asyncio
from websockets.asyncio.client import connect

from utils import debuggable

@dataclass
class RunnerState:
    stdout: str
    stderr: str
    finished: bool

    message: Message

    def update_message(self):
        out = "Exécution en cours...\n" if not self.finished else "Exécution terminée\n"

        if self.stdout != "":
            out += "-# STDOUT\n"
            out += "```\n"
            out += self.stdout
            out += "```\n"

        if self.stderr != "":
            out += "-# STDOUT\n"
            out += "```\n"
            out += self.stderr
            out += "```\n"

        self.message.edit(out)


class Code(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repeat = True

    @commands.command()
    @debuggable
    async def run(self, ctx, code: str):
        code = """
        fn main() {
            println!("Hello, world!");
        }
        """.replace("\n", "\\n").replace("\"", "\\\"")

        with ctx.message.channel.typing():
            async with connect("wss://play.rust-lang.org/websocket") as websocket:
                message = await ctx.send("Exécution en cours...")
                state = RunnerState(stdout="", stderr="", finished=false, message=message)

                await websocket.send('{"type":"websocket/connected","payload":{"iAcceptThisIsAnUnsupportedApi":true},"meta":{"websocket":true,"sequenceNumber":0}}')
                await websocket.recv()
                await websocket.recv()

                req = '{"type":"output/execute/wsExecuteRequest","payload":{"channel":"stable","mode":"debug","edition":"2024","crateType":"bin","tests":false,"code":"' \
                    + code \
                    + '","backtrace":false},"meta":{"websocket":true,"sequenceNumber":1}}'
                await websocket.send(req)

                async for message in websocket:
                    res = json.loads(message)

                    match res["type"]:
                        case "output/execute/wsExecuteEnd":
                            state.finished = True
                            state.update_message()
                            break

                        case "output/execute/wsExecuteStderr":
                            state.stderr += res["payload"]
                            state.update_message()

                        case "output/execute/wsExecuteStdout":
                            state.stdout += res["payload"]
                            state.update_message()


def setup(bot):
    bot.add_cog(Code(bot))
