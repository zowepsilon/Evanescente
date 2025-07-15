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
    out: str
    finished: bool

    message: Message

    async def update_message(self):
        out = "Exécution en cours...\n" if not self.finished else "Exécution terminée\n"

        self.out = '\n'.join(self.out.split('\n')[-20:])

        if self.out != "":
            out += "```rust\n"
            out += self.out.replace("`", "​`")
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

        code = code.replace("\\", "\\\\").replace("\n", "\\n").replace("\"", "\\\"")

        TIMEOUT = 10
        message = await ctx.send("Exécution en cours...")

        async with connect("wss://play.rust-lang.org/websocket") as websocket:
            state = RunnerState(out="", finished=False, message=message)

            await websocket.send('{"type":"websocket/connected","payload":{"iAcceptThisIsAnUnsupportedApi":true},"meta":{"websocket":true,"sequenceNumber":0}}')
            await websocket.recv()
            await websocket.recv()

            req = '{"type":"output/execute/wsExecuteRequest","payload":{"channel":"nightly","mode":"debug","edition":"2024","crateType":"bin","tests":false,"code":"' \
                + code \
                + '","backtrace":false},"meta":{"websocket":true,"sequenceNumber":1}}'
            await websocket.send(req)
            
            try:
                async with asyncio.timeout(TIMEOUT):
                    async for raw in websocket:
                        res = json.loads(raw)

                        match res["type"]:
                            case "output/execute/wsExecuteEnd":
                                state.finished = True
                                await state.update_message()
                                break

                            case "output/execute/wsExecuteStderr":
                                payload = res["payload"]
                                if payload[0] == '\r':
                                    state.out = '\n'.join(state.out.split('\n')[:-1])
                                    payload = payload[1:]

                                state.out += payload
                                await state.update_message()

                            case "output/execute/wsExecuteStdout":
                                payload = res["payload"]
                                if payload[0] == '\r':
                                    state.out = '\n'.join(state.out.split('\n')[:-1])
                                    payload = payload[1:]

                                state.out += payload
                                await state.update_message()

                            case "output/execute/wsExecuteStatus" | "output/execute/wsExecuteBegin":
                                pass
                            case _:
                                print("UNKNOWN REQUEST TYPE:", res["type"])
                                print("REQUEST :", res)

            except asyncio.TimeoutError:
                state.finished = True
                await state.update_message()

def setup(bot):
    bot.add_cog(Code(bot))
