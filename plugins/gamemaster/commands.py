from core import DCSServerBot, Plugin, utils, Status, Server, Player
from discord.ext import commands
from .listener import GameMasterEventListener


class GameMaster(Plugin):

    @commands.command(description='Send a chat message to a running DCS instance', usage='<message>', hidden=True)
    @utils.has_role('DCS')
    @commands.guild_only()
    async def chat(self, ctx, *args):
        server: Server = await self.bot.get_server(ctx)
        if server and server.status == Status.RUNNING:
            server.sendtoDCS({
                "command": "sendChatMessage",
                "channel": ctx.channel.id,
                "message": ' '.join(args),
                "from": ctx.message.author.display_name
            })

    @commands.command(description='Sends a popup message', usage='<coal.|user> [time] <msg>')
    @utils.has_roles(['DCS Admin', 'GameMaster'])
    @commands.guild_only()
    async def popup(self, ctx, to, *args):
        server: Server = await self.bot.get_server(ctx)
        if server:
            if server.status != Status.RUNNING:
                await ctx.send(f"Mission is {server.status.name.lower()}, message discarded.")
                return
            if len(args) > 0:
                if args[0].isnumeric():
                    time = int(args[0])
                    i = 1
                else:
                    time = -1
                    i = 0
                message = ' '.join(args[i:])
                if to.lower() not in ['all', 'red', 'blue']:
                    player: Player = server.get_player(name=to, active=True)
                    if player:
                        player.sendPopupMessage(message, time, ctx.message.author.display_name)
                    else:
                        await ctx.send(f'Can\'t find player "{to}" or player is not in an active unit.')
                        return
                else:
                    server.sendPopupMessage(message, time, ctx.message.author.display_name)
                await ctx.send('Message sent.')
            else:
                await ctx.send(f"Usage: {ctx.prefix}popup all|red|blue|user [time] <message>")

    @commands.command(description='Set or clear a flag inside the mission', usage='<flag> [value]')
    @utils.has_roles(['DCS Admin', 'GameMaster'])
    @commands.guild_only()
    async def flag(self, ctx, flag: int, value: int = None):
        server: Server = await self.bot.get_server(ctx)
        if server and server.status in [Status.RUNNING, Status.PAUSED]:
            if value is not None:
                server.sendtoDCS({
                    "command": "setFlag",
                    "channel": ctx.channel.id,
                    "flag": flag,
                    "value": value
                })
                await ctx.send(f"Flag {flag} set to {value}.")
            else:
                data = await server.sendtoDCSSync({"command": "getFlag", "flag": flag})
                await ctx.send(f"Flag {flag} has value {data['value']}.")
        else:
            await ctx.send(f"Mission is {server.status.name.lower()}, can't set/get flag.")

    @commands.command(description='Set or get a mission variable', usage='<name> [value]')
    @utils.has_roles(['DCS Admin', 'GameMaster'])
    @commands.guild_only()
    async def variable(self, ctx, name: str, value: str = None):
        server: Server = await self.bot.get_server(ctx)
        if server and server.status in [Status.RUNNING, Status.PAUSED]:
            if value is not None:
                server.sendtoDCS({
                    "command": "setVariable",
                    "channel": ctx.channel.id,
                    "name": name,
                    "value": value
                })
                await ctx.send(f"Variable {name} set to {value}.")
            else:
                data = await server.sendtoDCSSync({"command": "getVariable", "name": name})
                if 'value' in data:
                    await ctx.send(f"Variable {name} has value {data['value']}.")
                else:
                    await ctx.send(f"Variable {name} is not set.")
        else:
            await ctx.send(f"Mission is {server.status.name.lower()}, can't set/get variable.")

    @commands.command(description='Calls any function inside the mission', usage='<script>')
    @utils.has_roles(['DCS Admin', 'GameMaster'])
    @commands.guild_only()
    async def do_script(self, ctx, *script):
        server: Server = await self.bot.get_server(ctx)
        if server and server.status in [Status.RUNNING, Status.PAUSED]:
            server.sendtoDCS({
                "command": "do_script",
                "script": ' '.join(script)
            })
            await ctx.send('Command sent.')
        else:
            await ctx.send(f"Mission is {server.status.name.lower()}, command discarded.")

    @commands.command(description='Loads a lua file into the mission', usage='<file>')
    @utils.has_roles(['DCS Admin', 'GameMaster'])
    @commands.guild_only()
    async def do_script_file(self, ctx, filename):
        server: Server = await self.bot.get_server(ctx)
        if server and server.status in [Status.RUNNING, Status.PAUSED]:
            server.sendtoDCS({
                "command": "do_script_file",
                "file": filename.replace('\\', '/')
            })
            await ctx.send('Command sent.')
        else:
            await ctx.send(f"Mission is {server.status.name.lower()}, command discarded.")


async def setup(bot: DCSServerBot):
    await bot.add_cog(GameMaster(bot, GameMasterEventListener))
