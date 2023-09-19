import discord
import json
from core import DCSServerBot, Plugin, PluginRequiredError, utils, Server, Player, TEventListener, Status, \
    PluginInstallationError
from discord.ext import tasks, commands
from os import path
from typing import Optional, TYPE_CHECKING, Type
from .listener import MessageOfTheDayListener

if TYPE_CHECKING:
    from core import DCSServerBot


class MessageOfTheDay(Plugin):

    def __init__(self, bot: DCSServerBot, eventlistener: Type[TEventListener] = None):
        super().__init__(bot, eventlistener)
        if not self.locals:
            raise PluginInstallationError(reason=f"No {self.plugin_name}.json file found!", plugin=self.plugin_name)
        self.last_nudge = dict[str, int]()
        self.nudge.start()

    async def cog_unload(self):
        self.nudge.cancel()
        await super().cog_unload()

    def migrate(self, version: str):
        if version != '1.1' or not path.exists('config/motd.json'):
            return
        with open('config/motd.json') as file:
            old = json.load(file)
            if 'on_event' not in old['configs'][0]:
                return
        new = {
            "configs": []
        }
        for oldc in old['configs']:
            newc = dict()
            if 'installation' in oldc:
                newc['installation'] = oldc['installation']
            if 'on_event' in oldc:
                event = 'on_' + oldc['on_event']
                newc[event] = dict()
                if 'message' in oldc:
                    newc[event]['message'] = oldc['message']
                if 'display_type' in oldc:
                    newc[event]['display_type'] = oldc['display_type']
                if 'display_time' in oldc:
                    newc[event]['display_time'] = oldc['display_time']
            new['configs'].append(newc)
        with open('config/motd.json', 'w') as file:
            json.dump(new, file, indent=2)
            self.log.info('  => config/motd.json migrated to new format.')

    def send_message(self, message: str, server: Server, config: dict, player: Optional[Player] = None):
        if config['display_type'].lower() == 'chat':
            if player:
                player.sendChatMessage(message)
            else:
                server.sendChatMessage(message)
        elif config['display_type'].lower() == 'popup':
            timeout = config['display_time'] if 'display_time' in config else self.bot.config['BOT']['MESSAGE_TIMEOUT']
            if player:
                player.sendPopupMessage(message, timeout)
            else:
                server.sendPopupMessage(message, timeout)
                if 'sound' in config:
                    server.playSound(config['sound'])

    @commands.command(description='Test MOTD', usage='[-join | -birth | -nudge]', hidden=True)
    @utils.has_roles(['DCS Admin'])
    @commands.guild_only()
    async def motd(self, ctx, option: str, member: Optional[discord.Member] = None):
        server: Server = await self.bot.get_server(ctx)
        config = self.get_config(server)
        if not config:
            await ctx.send('No configuration for MOTD found.')
            return
        if server and server.status in [Status.RUNNING, Status.PAUSED]:
            message = None
            if 'join' in option:
                message = self.eventlistener.on_join(config)
            elif 'birth' in option:
                if not member:
                    await ctx.send(f'Usage: {ctx.prefix}{option} @member')
                    return
                player: Player = server.get_player(discord_id=member.id)
                if not player:
                    await ctx.send("Player {} is currently not logged in.".format(utils.escape_string(member.display_name)))
                    return
                message = await self.eventlistener.on_birth(config, server, player)
            elif 'nudge' in option:
                # TODO
                pass
            if message:
                await ctx.send(f"```{message}```")
        else:
            await ctx.send(f"Mission is {server.status.name.lower()}, can't test MOTD.")

    @tasks.loop(minutes=1.0)
    async def nudge(self):
        def process_message(message: str, server: Server, config: dict):
            self.send_message(message, server, config)

        try:
            for server_name, server in self.bot.servers.items():
                config = self.get_config(server)
                if server.status != Status.RUNNING or not config or 'nudge' not in config:
                    continue
                config = config['nudge']
                if server.name not in self.last_nudge:
                    self.last_nudge[server.name] = server.current_mission.mission_time
                elif server.current_mission.mission_time - self.last_nudge[server.name] > config['delay']:
                    if 'message' in config:
                        message = utils.format_string(config['message'], server=server)
                        process_message(message, server, config)
                    elif 'messages' in config:
                        for cfg in config['messages']:
                            message = utils.format_string(cfg['message'], server=server)
                            process_message(message, server, cfg)
                    self.last_nudge[server.name] = server.current_mission.mission_time
        except Exception as ex:
            self.log.exception(ex)


async def setup(bot: DCSServerBot):
    if 'mission' not in bot.plugins:
        raise PluginRequiredError('mission')
    await bot.add_cog(MessageOfTheDay(bot, MessageOfTheDayListener))
