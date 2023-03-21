import asyncio
import shlex
import string
import subprocess
from core import EventListener, utils, Server, Player, Status
from os import path


class SchedulerListener(EventListener):

    def _run(self, server: Server, method: str) -> None:
        if method.startswith('load:'):
            server.sendtoDCS({
                "command": "do_script_file",
                "file": method[5:].strip().replace('\\', '/')
            })
        elif method.startswith('lua:'):
            server.sendtoDCS({
                "command": "do_script",
                "script": method[4:].strip()
            })
        elif method.startswith('call:'):
            server.sendtoDCS({
                "command": method[5:].strip()
            })
        elif method.startswith('run:'):
            cmd = method[4:].strip()
            dcs_installation = path.normpath(path.expandvars(self.bot.config['DCS']['DCS_INSTALLATION']))
            dcs_home = path.normpath(path.expandvars(self.bot.config[server.installation]['DCS_HOME']))
            cmd = utils.format_string(cmd, dcs_installation=dcs_installation, dcs_home=dcs_home,
                                      server=server, config=self.bot.config)
            self.log.debug('Launching command: ' + cmd)
            subprocess.run(shlex.split(cmd), shell=True)

    async def registerDCSServer(self, data: dict) -> None:
        server: Server = self.bot.servers[data['server_name']]
        config = self.plugin.get_config(server)
        await self.plugin.init_extensions(server, config)
        for ext in server.extensions.values():
            if not ext.is_running():
                await ext.startup()

    async def onPlayerStart(self, data: dict) -> None:
        if data['id'] == 1 or 'ucid' not in data:
            return
        server: Server = self.bot.servers[data['server_name']]
        if server.restart_pending:
            player: Player = server.get_player(id=data['id'])
            player.sendChatMessage("*** Mission is about to be restarted soon! ***")

    async def onGameEvent(self, data: dict) -> None:
        async def _process(server: Server, what: dict) -> None:
            config = self.plugin.get_config(server)
            if 'shutdown' in what['command']:
                await server.shutdown()
                message = 'shut down DCS server'
                if 'user' not in what:
                    message = string.capwords(self.plugin_name) + ' ' + message
                await self.bot.audit(message, server=server, user=what['user'] if 'user' in what else None)
            if 'restart' in what['command']:
                if server.status == Status.SHUTDOWN:
                    await self.plugin.launch_dcs(server, config)
                elif server.status == Status.STOPPED:
                    if self.plugin.is_mission_change(server, config):
                        for ext in server.extensions.values():
                            await ext.beforeMissionLoad()
                        if 'settings' in config['restart']:
                            await self.plugin.change_mizfile(server, config)
                        await server.start()
                    message = 'started DCS server'
                    if 'user' not in what:
                        message = string.capwords(self.plugin_name) + ' ' + message
                    await self.bot.audit(message, server=server, user=what.get('user', None))
                elif server.status in [Status.RUNNING, Status.PAUSED]:
                    if self.plugin.is_mission_change(server, config):
                        await server.stop()
                        for ext in server.extensions.values():
                            await ext.beforeMissionLoad()
                        if 'settings' in config['restart']:
                            await self.plugin.change_mizfile(server, config)
                        await server.start()
                    else:
                        await server.current_mission.restart()
                    message = f'restarted mission {server.current_mission.display_name}'
                    if 'user' not in what:
                        message = string.capwords(self.plugin_name) + ' ' + message
                    await self.bot.audit(message, server=server, user=what.get('user', None))
            elif what['command'] == 'rotate':
                await server.loadNextMission()
                if self.plugin.is_mission_change(server, config):
                    await server.stop()
                    for ext in server.extensions.values():
                        await ext.beforeMissionLoad()
                    if 'settings' in config['restart']:
                        await self.plugin.change_mizfile(server, config)
                    await server.start()
                await self.bot.audit(f"{string.capwords(self.plugin_name)} rotated to mission "
                                     f"{server.current_mission.display_name}", server=server)
            elif what['command'] == 'load':
                await server.loadMission(what['id'])
                message = f'loaded mission {server.current_mission.display_name}'
                if 'user' not in what:
                    message = string.capwords(self.plugin_name) + ' ' + message
                await self.bot.audit(message, server=server, user=what['user'] if 'user' in what else None)
            elif what['command'] == 'preset':
                await server.stop()
                for preset in what['preset']:
                    await self.plugin.change_mizfile(server, config, preset)
                await server.start()
                await self.bot.audit(f"changed preset to {what['preset']}", server=server, user=what['user'])
            server.restart_pending = False

        server: Server = self.bot.servers[data['server_name']]
        if data['eventName'] == 'disconnect':
            if not server.is_populated() and server.on_empty:
                await _process(server, server.on_empty)
                server.on_empty = dict()
        elif data['eventName'] == 'mission_end':
            self.bot.sendtoBot({"command": "onMissionEnd", "server_name": server.name})
            if server.on_mission_end:
                await _process(server, server.on_mission_end)
                server.on_mission_end = dict()

    async def onSimulationStart(self, data: dict) -> None:
        server: Server = self.bot.servers[data['server_name']]
        config = self.plugin.get_config(server)
        if config and 'onMissionStart' in config:
            self._run(server, config['onMissionStart'])

    async def onMissionLoadEnd(self, data: dict) -> None:
        server: Server = self.bot.servers[data['server_name']]
        server.restart_pending = False
        for ext in server.extensions.values():
            if ext.is_running():
                await ext.onMissionLoadEnd(data)

    async def onMissionEnd(self, data: dict) -> None:
        server: Server = self.bot.servers[data['server_name']]
        config = self.plugin.get_config(server)
        if config and 'onMissionEnd' in config:
            self._run(server, config['onMissionEnd'])

    async def onSimulationStop(self, data: dict) -> None:
        server: Server = self.bot.servers[data['server_name']]
        for ext in server.extensions.values():
            if ext.is_running():
                await ext.shutdown(data)

    async def onShutdown(self, data: dict) -> None:
        server: Server = self.bot.servers[data['server_name']]
        config = self.plugin.get_config(server)
        if config and 'onShutdown' in config:
            self._run(server, config['onShutdown'])
