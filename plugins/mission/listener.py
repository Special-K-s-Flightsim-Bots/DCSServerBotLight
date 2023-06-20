from __future__ import annotations
import discord
from core import utils, EventListener, PersistentReport, Plugin, Report, Status, Side, Mission, Player, Channel, \
    DataObjectFactory, event, chat_command
from datetime import datetime
from discord.ext import tasks
from queue import Queue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Server


class MissionEventListener(EventListener):
    EVENT_TEXTS = {
        Side.BLUE: {
            'takeoff': '```ansi\n\u001b[0;34mBLUE player {} took off from {}.```',
            'landing': '```ansi\n\u001b[0;34mBLUE player {} landed at {}.```',
            'eject': '```ansi\n\u001b[0;34mBLUE player {} ejected.```',
            'crash': '```ansi\n\u001b[0;34mBLUE player {} crashed.```',
            'pilot_death': '```ansi\n\u001b[0;34mBLUE player {} died.```',
            'kill': '```ansi\n\u001b[0;34mBLUE {} in {} killed {} {} in {} with {}.```',
            'friendly_fire': '```ansi\n\u001b[1;33mBLUE {} FRIENDLY FIRE onto {} with {}.```',
            'self_kill': '```ansi\n\u001b[0;34mBLUE player {} killed themselves - Ooopsie!```',
            'change_slot': '```ansi\n\u001b[0;34m{} player {} occupied {} {}```',
            'disconnect': '```ansi\n\u001b[0;34mBLUE player {} disconnected```'
        },
        Side.RED: {
            'takeoff': '```ansi\n\u001b[0;31mRED player {} took off from {}.```',
            'landing': '```ansi\n\u001b[0;31mRED player {} landed at {}.```',
            'eject': '```ansi\n\u001b[0;31mRED player {} ejected.```',
            'crash': '```ansi\n\u001b[0;31mRED player {} crashed.```',
            'pilot_death': '```ansi\n\u001b[0;31mRED player {} died.```',
            'kill': '```ansi\n\u001b[0;31mRED {} in {} killed {} {} in {} with {}.```',
            'friendly_fire': '```ansi\n\u001b[1;33mRED {} FRIENDLY FIRE onto {} with {}.```',
            'self_kill': '```ansi\n\u001b[0;31mRED player {} killed themselves - Ooopsie!```',
            'change_slot': '```ansi\n\u001b[0;31m{} player {} occupied {} {}```',
            'disconnect': '```ansi\n\u001b[0;31mRED player {} disconnected```'
        },
        Side.SPECTATOR: {
            'connect': '```\nPlayer {} connected to server```',
            'disconnect': '```\nPlayer {} disconnected```',
            'spectators': '```\n{} player {} returned to Spectators```',
            'crash': '```\nPlayer {} crashed.```',
            'pilot_death': '```\n[Player {} died.```',
            'kill': '```\n{} in {} killed {} {} in {} with {}.```',
            'friendly_fire': '```ansi\n\u001b[1;33m{} FRIENDLY FIRE onto {} with {}.```'
        },
        Side.UNKNOWN: {
            'kill': '```\n{} in {} killed {} {} in {} with {}.```'
        }
    }

    def __init__(self, plugin: Plugin):
        super().__init__(plugin)
        self.queue: dict[discord.TextChannel, Queue[str]] = dict()
        self.player_embeds: dict[str, bool] = dict()
        self.mission_embeds: dict[str, bool] = dict()
        self.print_queue.start()
        self.update_player_embed.start()
        self.update_mission_embed.start()

    async def shutdown(self):
        self.print_queue.cancel()
        await self.work_queue(True)
        self.update_player_embed.cancel()
        self.update_mission_embed.cancel()

    async def work_queue(self, flush: bool = False):
        for channel in self.queue.keys():
            if self.queue[channel].empty():
                continue
            messages: set = set()
            while not self.queue[channel].empty():
                messages.add(self.queue[channel].get())
                if messages.__sizeof__() > 1900:
                    if not flush:
                        break
                    await channel.send(''.join(messages))
                    messages.clear()
            if messages:
                await channel.send(''.join(messages))

    @tasks.loop(seconds=2)
    async def print_queue(self):
        try:
            await self.work_queue()
            if self.print_queue.seconds == 10:
                self.print_queue.change_interval(seconds=2)
        except discord.errors.DiscordException:
            self.print_queue.change_interval(seconds=10)
        except Exception as ex:
            self.log.debug("Exception in print_queue(): " + str(ex))

    @tasks.loop(seconds=5)
    async def update_player_embed(self):
        for server_name, update in self.player_embeds.items():
            if update:
                server = self.bot.servers[server_name]
                if not self.bot.config.getboolean(server.installation, 'COALITIONS'):
                    report = PersistentReport(self.bot, self.plugin_name, 'players.json', server, 'players_embed')
                    await report.render(server=server)
                self.player_embeds[server_name] = False

    @tasks.loop(seconds=5)
    async def update_mission_embed(self):
        for server_name, update in self.mission_embeds.items():
            if update:
                server = self.bot.servers[server_name]
                if not server.settings:
                    return
                players = server.get_active_players()
                num_players = len(players) + 1
                report = PersistentReport(self.bot, self.plugin_name, 'serverStatus.json', server, 'mission_embed')
                await report.render(server=server, num_players=num_players)
                self.mission_embeds[server_name] = False

    @print_queue.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @event(name="sendMessage")
    async def sendMessage(self, server: Server, data: dict) -> None:
        if int(data['channel']) == -1:
            channel = server.get_channel(Channel.EVENTS)
        else:
            channel = self.bot.get_channel(int(data['channel']))
        if channel:
            await channel.send(data['message'])

    @event(name="sendEmbed")
    async def sendEmbed(self, server: Server, data: dict) -> None:
        embed = utils.format_embed(data)
        if 'id' in data and len(data['id']) > 0:
            channel = int(data['channel'])
            if channel == -1:
                channel = Channel.STATUS
            await server.setEmbed(data['id'], embed, channel_id=channel)
            return
        else:
            if int(data['channel']) == -1:
                channel = server.get_channel(Channel.EVENTS)
            else:
                channel = self.bot.get_channel(int(data['channel']))
            if channel:
                await channel.send(embed=embed)

    def send_dcs_event(self, server: Server, message: str) -> None:
        events_channel = server.get_channel(Channel.EVENTS)
        if events_channel:
            if events_channel not in self.queue:
                self.queue[events_channel] = Queue()
            self.queue[events_channel].put(message)

    def display_mission_embed(self, server: Server):
        self.mission_embeds[server.name] = True

    # Display the list of active players
    def display_player_embed(self, server: Server):
        self.player_embeds[server.name] = True

    @event(name="callback")
    async def callback(self, server: Server, data: dict):
        if data['subcommand'] in ['startMission', 'restartMission', 'pause', 'shutdown']:
            data['command'] = data['subcommand']
            server.sendtoDCS(data)

    @event(name="registerDCSServer")
    async def registerDCSServer(self, server: Server, data: dict) -> None:
        # the server is starting up
        if not data['channel'].startswith('sync-'):
            return
        # no mission is registered with the server, set the state to STOPPED
        if 'current_mission' not in data:
            server.status = Status.STOPPED
            return
        # the server was started already, but the bot wasn't
        if not server.current_mission:
            server.current_mission = DataObjectFactory().new(Mission.__name__, bot=self.bot, server=server,
                                                             map=data['current_map'], name=data['current_mission'])

        if 'players' not in data:
            data['players'] = []
            server.status = Status.STOPPED
        else:
            server.status = Status.PAUSED if data['pause'] is True else Status.RUNNING
        server.current_mission.update(data)
        server.afk.clear()
        for p in data['players']:
            if p['id'] == 1:
                continue
            player: Player = DataObjectFactory().new(Player.__name__, bot=self.bot, server=server, id=p['id'],
                                                     name=p['name'], active=p['active'], side=Side(p['side']),
                                                     ucid=p['ucid'], slot=int(p['slot']), sub_slot=p['sub_slot'],
                                                     unit_callsign=p['unit_callsign'], unit_name=p['unit_name'],
                                                     unit_type=p['unit_type'], group_id=p['group_id'],
                                                     group_name=p['group_name'], banned=False)
            server.add_player(player)
            if Side(p['side']) == Side.SPECTATOR:
                server.afk[player.ucid] = datetime.now()
        self.display_mission_embed(server)
        self.display_player_embed(server)

    @event(name="onMissionLoadBegin")
    async def onMissionLoadBegin(self, server: Server, data: dict) -> None:
        server.status = Status.LOADING
        if not server.current_mission:
            server.current_mission = DataObjectFactory().new(Mission.__name__, bot=self.bot, server=server,
                                                             map=data['current_map'], name=data['current_mission'])
        server.current_mission.update(data)
        server.players = dict[int, Player]()
        if server.settings:
            self.display_mission_embed(server)
        self.display_player_embed(server)

    @event(name="onMissionLoadEnd")
    async def onMissionLoadEnd(self, server: Server, data: dict) -> None:
        server.current_mission.update(data)
        self.display_mission_embed(server)

    @event(name="onSimulationStart")
    async def onSimulationStart(self, server: Server, data: dict) -> None:
        server.status = Status.PAUSED
        self.display_mission_embed(server)

    @event(name="onSimulationStop")
    async def onSimulationStop(self, server: Server, data: dict) -> None:
        server.status = Status.STOPPED
        self.display_mission_embed(server)

    @event(name="onSimulationPause")
    async def onSimulationPause(self, server: Server, data: dict) -> None:
        server.status = Status.PAUSED
        self.display_mission_embed(server)

    @event(name="onSimulationResume")
    async def onSimulationResume(self, server: Server, data: dict) -> None:
        server.status = Status.RUNNING
        self.display_mission_embed(server)

    @event(name="onPlayerConnect")
    async def onPlayerConnect(self, server: Server, data: dict) -> None:
        if data['id'] == 1:
            return
        self.send_dcs_event(server, self.EVENT_TEXTS[Side.SPECTATOR]['connect'].format(data['name']))
        player: Player = server.get_player(ucid=data['ucid'])
        if not player or player.id == 1:
            player: Player = DataObjectFactory().new(Player.__name__, bot=self.bot, server=server, id=data['id'],
                                                     name=data['name'], active=data['active'], side=Side(data['side']),
                                                     ucid=data['ucid'], banned=False)
            server.add_player(player)
        else:
            player.update(data)

    @event(name="onPlayerStart")
    async def onPlayerStart(self, server: Server, data: dict) -> None:
        if data['id'] == 1 or 'ucid' not in data:
            return
        player: Player = server.get_player(id=data['id'])
        # unlikely, but can happen if the bot was restarted during a mission restart
        if not player:
            player = DataObjectFactory().new(Player.__name__, bot=self.bot, server=server, id=data['id'],
                                             name=data['name'], active=data['active'], side=Side(data['side']),
                                             ucid=data['ucid'], banned=False)
            server.add_player(player)
        else:
            player.update(data)
        # add the player to the afk list
        server.afk[player.ucid] = datetime.now()
        self.display_mission_embed(server)
        self.display_player_embed(server)

    @event(name="onPlayerStop")
    async def onPlayerStop(self, server: Server, data: dict) -> None:
        if data['id'] == 1:
            return
        player: Player = server.get_player(id=data['id'])
        if player:
            player.active = False
            if player.ucid in server.afk:
                del server.afk[player.ucid]
        self.display_mission_embed(server)
        self.display_player_embed(server)

    @event(name="onPlayerChangeSlot")
    async def onPlayerChangeSlot(self, server: Server, data: dict) -> None:
        if 'side' not in data:
            return
        player: Player = server.get_player(id=data['id'])
        if not player:
            return
        try:
            if Side(data['side']) != Side.SPECTATOR:
                if player.ucid in server.afk:
                    del server.afk[player.ucid]
                self.send_dcs_event(server, self.EVENT_TEXTS[Side(data['side'])]['change_slot'].format(
                    player.side.name if player.side != Side.SPECTATOR else 'NEUTRAL',
                    data['name'], Side(data['side']).name, data['unit_type']))
            else:
                server.afk[player.ucid] = datetime.now()
                self.send_dcs_event(server, self.EVENT_TEXTS[Side.SPECTATOR]['spectators'].format(player.side.name,
                                                                                                     data['name']))
        finally:
            if player:
                player.update(data)
            self.display_player_embed(server)

    @event(name="onGameEvent")
    async def onGameEvent(self, server: Server, data: dict) -> None:
        # ignore game events until the server is not initialized correctly
        if server.status not in [Status.RUNNING, Status.STOPPED]:
            return
        if data['eventName'] in ['mission_end', 'connect', 'change_slot']:  # these events are handled differently
            return
        elif data['eventName'] == 'disconnect':
            if data['arg1'] == 1:
                return
            player = server.get_player(id=data['arg1'])
            if not player:
                return
            try:
                self.send_dcs_event(server, self.EVENT_TEXTS[player.side]['disconnect'].format(player.name))
            finally:
                player.active = False
                if player.ucid in server.afk:
                    del server.afk[player.ucid]
                self.display_mission_embed(server)
                self.display_player_embed(server)
        elif data['eventName'] == 'friendly_fire' and data['arg1'] != data['arg3']:
            player1 = server.get_player(id=data['arg1'])
            if data['arg3'] != -1:
                player2 = server.get_player(id=data['arg3'])
            else:
                # TODO: remove if issue with Forrestal is fixed
                return
#                player2 = None
            self.send_dcs_event(server, self.EVENT_TEXTS[player1.side][data['eventName']].format(
                'player ' + player1.name, ('player ' + player2.name) if player2 is not None else 'AI',
                data['arg2'] or 'Cannon/Bomblet'))
        elif data['eventName'] == 'self_kill':
            player = server.get_player(id=data['arg1']) if data['arg1'] != -1 else None
            self.send_dcs_event(server, self.EVENT_TEXTS[player.side][data['eventName']].format(player.name))
        elif data['eventName'] == 'kill':
            # Player is not an AI
            player1 = server.get_player(id=data['arg1']) if data['arg1'] != -1 else None
            player2 = server.get_player(id=data['arg4']) if data['arg4'] != -1 else None
            self.send_dcs_event(server, self.EVENT_TEXTS[Side(data['arg3'])][data['eventName']].format(
                ('player ' + player1.name) if player1 is not None else 'AI',
                data['arg2'] or 'SCENERY', Side(data['arg6']).name,
                ('player ' + player2.name) if player2 is not None else 'AI',
                data['arg5'] or 'SCENERY', data['arg7'] or 'Cannon/Bomblet'))
            # report teamkills from players to admins (only on public servers)
            if server.is_public() and player1 and player2 and data['arg1'] != data['arg4'] \
                    and data['arg3'] == data['arg6']:
                name = 'Player ' + player1.display_name
                await server.get_channel(Channel.ADMIN).send(
                    f'{name} (ucid={player1.ucid}) is killing team members. Please investigate.'
                )
        elif data['eventName'] in ['takeoff', 'landing', 'crash', 'eject', 'pilot_death']:
            if data['arg1'] != -1:
                player = server.get_player(id=data['arg1'])
                if not player:
                    return
                if data['eventName'] in ['takeoff', 'landing']:
                    self.send_dcs_event(server, self.EVENT_TEXTS[player.side][data['eventName']].format(
                        player.name, data['arg3'] if len(data['arg3']) > 0 else 'ground'))
                else:
                    self.send_dcs_event(server,
                                        self.EVENT_TEXTS[player.side][data['eventName']].format(player.name))

    @chat_command(name="atis", usage="<airport>", help="display ATIS information")
    async def atis(self, server: Server, player: Player, params: list[str]):
        if len(params) == 0:
            player.sendChatMessage(f"Usage: -atis <airbase/code>")
            return
        name = ' '.join(params)
        for airbase in server.current_mission.airbases:
            if (name.casefold() in airbase['name'].casefold()) or (name.upper() == airbase['code']):
                response = await server.sendtoDCSSync({
                    "command": "getWeatherInfo",
                    "x": airbase['position']['x'],
                    "y": airbase['position']['y'],
                    "z": airbase['position']['z']
                })
                report = Report(self.bot, self.plugin_name, 'atis-ingame.json')
                env = await report.render(airbase=airbase, data=response)
                message = utils.embed_to_simpletext(env.embed)
                player.sendUserMessage(message, 30)
                return
        player.sendChatMessage(f"No ATIS information found for {name}.")
