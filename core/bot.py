import asyncio
import discord
import json
import platform
import socket
import string
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from core import utils, Server, Status, Channel, DataObjectFactory, DBConnection, Player
from datetime import datetime
from discord.ext import commands
from queue import Queue
from socketserver import BaseRequestHandler, ThreadingUDPServer
from typing import Callable, Optional, Tuple, Union
from .listener import EventListener


class DCSServerBot(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.member: Optional[discord.Member] = None
        self.version: str = kwargs['version']
        self.sub_version: str = kwargs['sub_version']
        self.listeners = {}
        self.eventListeners: list[EventListener] = []
        self.external_ip: Optional[str] = None
        self.udp_server = None
        self.servers: dict[str, Server] = dict()
        self.log = kwargs['log']
        self.config = kwargs['config']
        self.master: bool = self.config.getboolean('BOT', 'MASTER')
        self.master_only: bool = self.config.getboolean('BOT', 'MASTER_ONLY')
        plugins: str = self.config['BOT']['PLUGINS']
        if 'OPT_PLUGINS' in self.config['BOT']:
            plugins += ', ' + self.config['BOT']['OPT_PLUGINS']
        self.plugins: [str] = [p.strip() for p in set(plugins.split(','))]
        self.audit_channel = None
        self.synced: bool = False
        self.tree.on_error = self.on_app_command_error
        self.executor = ThreadPoolExecutor(thread_name_prefix='BotExecutor')

    async def close(self):
        await self.audit(message="DCSServerBotLight stopped.")
        await super().close()
        self.log.debug('Shutting down...')
        if self.udp_server:
            self.udp_server.shutdown()
            self.udp_server.server_close()
        self.log.debug('- Listener stopped.')
        self.executor.shutdown(wait=True)
        self.log.debug('- Executor stopped.')
        self.log.info('Shutdown complete.')

    def is_master(self) -> bool:
        return self.master

    def init_servers(self):
        for server_name, installation in utils.findDCSInstallations():
            if installation in self.config:
                server: Server = DataObjectFactory().new(
                    Server.__name__, bot=self, name=server_name, installation=installation,
                    host=self.config[installation]['DCS_HOST'], port=self.config[installation]['DCS_PORT'])
                self.servers[server_name] = server
                # TODO: can be removed if bug in net.load_next_mission() is fixed
                if 'listLoop' not in server.settings or not server.settings['listLoop']:
                    server.settings['listLoop'] = True

    async def register_servers(self):
        self.log.info('- Searching for running DCS servers, this might take a bit ...')
        servers = list(self.servers.values())
        timeout = (5 * len(self.servers)) if self.config.getboolean('BOT', 'SLOW_SYSTEM') else (3 * len(self.servers))
        ret = await asyncio.gather(
            *[server.sendtoDCSSync({"command": "registerDCSServer"}, timeout) for server in servers],
            return_exceptions=True
        )
        num = 0
        for i in range(0, len(servers)):
            if isinstance(ret[i], asyncio.TimeoutError):
                servers[i].status = Status.SHUTDOWN
                self.log.debug(f'  => Timeout while trying to contact DCS server "{servers[i].name}".')
            else:
                self.log.info(f'  => Running DCS server "{servers[i].name}" registered.')
                num += 1
        if num == 0:
            self.log.info('- No running servers found.')
        self.log.info('DCSServerBotLight started, accepting commands.')
        await self.audit(message="DCSServerBotLight started.")

    async def load_plugin(self, plugin: str) -> bool:
        try:
            await self.load_extension(f'plugins.{plugin}.commands')
            return True
        except ModuleNotFoundError:
            self.log.error(f'  - Plugin "{plugin}" not found!')
        except commands.ExtensionNotFound:
            self.log.error(f'  - No commands.py found for plugin "{plugin}"!')
        except commands.ExtensionAlreadyLoaded:
            self.log.warning(f'  - Plugin "{plugin} was already loaded"')
        except commands.ExtensionFailed as ex:
            self.log.error(f'  - {ex.original if ex.original else ex}')
        except Exception as ex:
            self.log.exception(ex)
        return False

    async def unload_plugin(self, plugin: str):
        try:
            await self.unload_extension(f'plugins.{plugin}.commands')
        except commands.ExtensionNotFound:
            self.log.debug(f'- No init.py found for plugin "{plugin}!"')
            pass

    async def reload_plugin(self, plugin: str):
        await self.unload_plugin(plugin)
        await self.load_plugin(plugin)

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        self.init_servers()
        await super().start(token, reconnect=reconnect)

    def check_roles(self, roles: list):
        for role in roles:
            config_roles = [x.strip() for x in self.config['ROLES'][role].split(',')]
            for discord_role in self.guilds[0].roles:
                if discord_role.name in config_roles:
                    config_roles.remove(discord_role.name)
            for bad_role in config_roles:
                self.log.error(f"  => Role {bad_role} not found in your Discord!")

    def check_channel(self, channel_id: int) -> bool:
        channel = self.get_channel(channel_id)
        if not channel:
            self.log.error(f'No channel with ID {channel_id} found!')
            return False
        channel_name = channel.name.encode(encoding='ASCII', errors='replace').decode()
        # name changes of the status channel will only happen with the correct permission
        ret = True
        permissions = channel.permissions_for(self.member)
        if not permissions.view_channel:
            self.log.error(f'  => Permission "View Channel" missing for channel {channel_name}')
            ret = False
        if not permissions.send_messages:
            self.log.error(f'  => Permission "Send Messages" missing for channel {channel_name}')
            ret = False
        if not permissions.read_messages:
            self.log.error(f'  => Permission "Read Messages" missing for channel {channel_name}')
            ret = False
        if not permissions.read_message_history:
            self.log.error(f'  => Permission "Read Message History" missing for channel {channel_name}')
            ret = False
        if not permissions.add_reactions:
            self.log.error(f'  => Permission "Add Reactions" missing for channel {channel_name}')
            ret = False
        if not permissions.attach_files:
            self.log.error(f'  => Permission "Attach Files" missing for channel {channel_name}')
            ret = False
        if not permissions.embed_links:
            self.log.error(f'  => Permission "Embed Links" missing for channel {channel_name}')
            ret = False
        if not permissions.manage_messages:
            self.log.error(f'  => Permission "Manage Messages" missing for channel {channel_name}')
            ret = False
        return ret

    def check_channels(self, installation: str):
        channels = ['ADMIN_CHANNEL', 'STATUS_CHANNEL', 'CHAT_CHANNEL']
        for c in channels:
            channel_id = int(self.config[installation][c])
            if channel_id != -1:
                self.check_channel(channel_id)

    async def on_ready(self):
        try:
            await self.wait_until_ready()
            if not self.external_ip:
                self.log.info(f'- Logged in as {self.user.name} - {self.user.id}')
                if len(self.guilds) > 1:
                    self.log.warning('  => YOUR BOT IS INSTALLED IN MORE THAN ONE GUILD. THIS IS NOT SUPPORTED!')
                    for guild in self.guilds:
                        self.log.warning(f'     - {guild.name}')
                    self.log.warning('  => Remove it from one guild and restart the bot.')
                self.member = self.guilds[0].get_member(self.user.id)
                self.external_ip = await utils.get_external_ip() if 'PUBLIC_IP' not in self.config['BOT'] else self.config['BOT']['PUBLIC_IP']
                self.log.info('- Checking Roles & Channels ...')
                self.check_roles(['Admin', 'DCS Admin', 'DCS', 'GameMaster'])
                for server in self.servers.values():
                    self.check_channels(server.installation)
                self.log.info('- Loading Plugins ...')
                for plugin in self.plugins:
                    if await self.load_plugin(plugin.lower()):
                        self.log.info(f'  => {string.capwords(plugin)} loaded.')
                    else:
                        self.log.info(f'  => {string.capwords(plugin)} NOT loaded.')
                if not self.synced:
                    self.log.debug('- Registering Discord Commands ...')
                    self.tree.copy_global_to(guild=self.guilds[0])
                    await self.tree.sync(guild=self.guilds[0])
                    self.synced = True
                    self.log.info('- Discord Commands registered.')
                if 'DISCORD_STATUS' in self.config['BOT']:
                    await self.change_presence(activity=discord.Game(name=self.config['BOT']['DISCORD_STATUS']))
                # start the UDP listener to accept commands from DCS
                self.loop.create_task(self.start_udp_listener())
                self.loop.create_task(self.register_servers())
            else:
                self.log.warning('- Discord connection re-established.')
                # maybe our external IP got changed...
                self.external_ip = await utils.get_external_ip() if 'PUBLIC_IP' not in self.config['BOT'] else self.config['BOT']['PUBLIC_IP']
        except Exception as ex:
            self.log.exception(ex)

    async def on_command_error(self, ctx: commands.Context, err: Exception):
        if isinstance(err, commands.CommandNotFound):
            pass
        elif isinstance(err, commands.NoPrivateMessage):
            await ctx.send(f"{ctx.command.name} can't be used in a DM.")
        elif isinstance(err, commands.MissingRequiredArgument):
            cmd = ctx.command.name + ' '
            if ctx.command.usage:
                cmd += ctx.command.usage
            else:
                cmd += ' '.join([f'<{name}>' if param.required else f'[{name}]' for name, param in ctx.command.params.items()])
            await ctx.send(f"Usage: {ctx.prefix}{cmd}")
        elif isinstance(err, commands.errors.CheckFailure):
            await ctx.send(f"You don't have the permission to use {ctx.command.name}!")
        elif isinstance(err, asyncio.TimeoutError):
            await ctx.send('A timeout occurred. Is the DCS server running?')
        else:
            self.log.exception(err)
            await ctx.send("An unknown exception occurred.")

    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.CommandNotFound):
            pass
        if isinstance(error, discord.app_commands.NoPrivateMessage):
            await interaction.response.send_message(f"{interaction.command.name} can't be used in a DM.")
        elif isinstance(error, discord.app_commands.CheckFailure):
            await interaction.response.send_message(f"You don't have the permission to use {interaction.command.name}!")
        elif isinstance(error, asyncio.TimeoutError):
            await interaction.response.send_message('A timeout occurred. Is the DCS server running?')
        else:
            self.log.exception(error)
            await interaction.response.send_message("An unknown exception occurred.")

    async def reload(self, plugin: Optional[str]):
        if plugin:
            await self.reload_plugin(plugin)
        else:
            for plugin in self.plugins:
                await self.reload_plugin(plugin)

    async def audit(self, message, *, user: Optional[Union[discord.Member, str]] = None, server: Optional[Server] = None):
        if not self.audit_channel:
            if 'AUDIT_CHANNEL' in self.config['BOT']:
                self.audit_channel = self.get_channel(int(self.config['BOT']['AUDIT_CHANNEL']))
        if self.audit_channel:
            if isinstance(user, str):
                member = None
            else:
                member = user
            embed = discord.Embed(color=discord.Color.blue())
            if member:
                embed.set_author(name=member.name + '#' + member.discriminator, icon_url=member.avatar)
                embed.set_thumbnail(url=member.avatar)
                message = f'<@{member.id}> ' + message
            elif not user:
                embed.set_author(name=self.member.name + '#' + self.member.discriminator,
                                 icon_url=self.member.avatar)
                embed.set_thumbnail(url=self.member.avatar)
            embed.description = message
            if isinstance(user, str):
                embed.add_field(name='UCID', value=user)
            if server:
                embed.add_field(name='Server', value=server.display_name)
            embed.set_footer(text=datetime.now().strftime("%d/%m/%y %H:%M:%S"))
            await self.audit_channel.send(embed=embed, allowed_mentions=discord.AllowedMentions(replied_user=False))

    def sendtoBot(self, message: dict):
        message['channel'] = '-1'
        msg = json.dumps(message)
        self.log.debug('HOST->HOST: {}'.format(msg))
        dcs_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        host = self.config['BOT']['HOST']
        if host == '0.0.0.0':
            host = '127.0.0.1'
        dcs_socket.sendto(msg.encode('utf-8'), (host, int(self.config['BOT']['PORT'])))
        dcs_socket.close()

    def get_channel(self, channel_id: int):
        return super().get_channel(channel_id) if channel_id != -1 else None
    
    def get_player_by_ucid(self, ucid: str) -> Optional[Player]:
        for server in self.servers.values():
            player = server.get_player(ucid=ucid, active=True)
            if player:
                return player
        return None

    def register_eventListener(self, listener: EventListener):
        self.log.debug(f'- Registering EventListener {type(listener).__name__}')
        self.eventListeners.append(listener)

    def unregister_eventListener(self, listener: EventListener):
        self.eventListeners.remove(listener)
        self.log.debug(f'- EventListener {type(listener).__name__} unregistered.')

    def register_server(self, data: dict) -> bool:
        installations = utils.findDCSInstallations(data['server_name'])
        if len(installations) == 0:
            self.log.error(f"No server {data['server_name']} found in any serverSettings.lua.\n"
                           f"Please check your server configurations!")
            return False
        _, installation = installations[0]
        if installation not in self.config:
            self.log.error(f"No section found for server {data['server_name']} in your dcsserverbot.ini.\n"
                           f"Please add a configuration for it!")
            return False
        self.log.debug(f"  => Registering DCS-Server \"{data['server_name']}\"")
        # check for protocol incompatibilities
        if data['hook_version'] != self.version:
            self.log.error('Server \"{}\" has wrong Hook version installed. Please update lua files and restart '
                           'server. Registration ignored.'.format(data['server_name']))
            return False
        # register the server in the internal datastructures
        if data['server_name'] in self.servers:
            server: Server = self.servers[data['server_name']]
        else:
            # a new server is to be registered
            server = self.servers[data['server_name']] = \
                DataObjectFactory().new(Server.__name__, bot=self, name=data['server_name'],
                                        installation=installation, host=self.config[installation]['DCS_HOST'],
                                        port=self.config[installation]['DCS_PORT'])
        # set the PID
        for exe in ['DCS_server.exe', 'DCS.exe']:
            server.process = utils.find_process(exe, server.installation)
            if server.process:
                break
        server.dcs_version = data['dcs_version']
        server.status = Status.STOPPED
        # update the database and check for server name changes
        with DBConnection() as cursor:
            cursor.execute('SELECT server_name FROM servers WHERE agent_host=? AND host=? AND port=?',
                           (platform.node(), data['host'], data['port']))
            if cursor.rowcount == 1:
                server_name = cursor.fetchone()[0]
                if server_name != data['server_name']:
                    if len(utils.findDCSInstallations(server_name)) == 0:
                        self.log.info(f"Auto-renaming server \"{server_name}\" to \"{data['server_name']}\"")
                        server.rename(data['server_name'])
                        if server_name in self.servers:
                            del self.servers[server_name]
                    else:
                        self.log.warning(
                            f"Registration of server \"{data['server_name']}\" aborted due to UDP port conflict.")
                        del self.servers[data['server_name']]
                        return False
            cursor.execute('INSERT INTO servers (server_name, agent_host, host, port) VALUES(?, ?, ?, ?) '
                           'ON CONFLICT (server_name) DO UPDATE SET agent_host=excluded.agent_host, '
                           'host=excluded.host, port=excluded.port, last_seen=CURRENT_TIMESTAMP',
                           (data['server_name'], platform.node(), data['host'], data['port']))
        self.log.debug(f"Server {server.name} initialized")
        return True

    async def get_server(self, ctx: Union[commands.Context, discord.Interaction, discord.Message, str]) -> Optional[Server]:
        if self.master and len(self.servers) == 1 and self.master_only:
            return list(self.servers.values())[0]
        for server_name, server in self.servers.items():
            if isinstance(ctx, commands.Context) or isinstance(ctx, discord.Interaction) \
                    or isinstance(ctx, discord.Message):
                if server.status == Status.UNREGISTERED:
                    continue
                channels = [Channel.ADMIN, Channel.STATUS]
                if int(self.config[server.installation][Channel.CHAT.value]) != -1:
                    channels.append(Channel.CHAT)
                for channel in channels:
                    if server.get_channel(channel).id == ctx.channel.id:
                        return server
            else:
                if server_name == ctx:
                    return server
        return None

    async def start_udp_listener(self):
        class RequestHandler(BaseRequestHandler):

            def handle(s):
                data = json.loads(s.request[0].strip())
                # ignore messages not containing server names
                if 'server_name' not in data:
                    self.log.warning('Message without server_name received: {}'.format(data))
                    return
                server_name = data['server_name']
                if server_name not in s.server.message_queue:
                    s.server.message_queue[server_name] = Queue()
                    s.server.executor.submit(s.process, server_name)
                s.server.message_queue[server_name].put(data)

            def process(s, server_name: str):
                data = s.server.message_queue[server_name].get()
                while len(data):
                    try:
                        self.log.debug('{}->HOST: {}'.format(data['server_name'], json.dumps(data)))
                        command = data['command']
                        if command == 'registerDCSServer':
                            if not self.register_server(data):
                                self.log.error(f"Error while registering server {server_name}. Exiting worker thread.")
                                return
                        elif (data['server_name'] not in self.servers or
                              self.servers[data['server_name']].status == Status.UNREGISTERED):
                            self.log.debug(f"Command {command} for unregistered server {data['server_name']} received, "
                                           f"ignoring.")
                            continue
                        if 'channel' in data and data['channel'].startswith('sync-'):
                            if data['channel'] in self.listeners:
                                f = self.listeners[data['channel']]
                                if not f.done():
                                    self.loop.call_soon_threadsafe(f.set_result, data)
                                if command != 'registerDCSServer':
                                    continue
                        for listener in self.eventListeners:
                            if command in listener.commands:
                                self.loop.call_soon_threadsafe(asyncio.create_task,
                                                               listener.processEvent(deepcopy(data)))
                    except Exception as ex:
                        self.log.exception(ex)
                    finally:
                        s.server.message_queue[server_name].task_done()
                        data = s.server.message_queue[server_name].get()

        class MyThreadingUDPServer(ThreadingUDPServer):
            def __init__(self, server_address: Tuple[str, int], request_handler: Callable[..., BaseRequestHandler]):
                # enable reuse, in case the restart was too fast and the port was still in TIME_WAIT
                MyThreadingUDPServer.allow_reuse_address = True
                MyThreadingUDPServer.max_packet_size = 65504
                self.message_queue: dict[str, Queue[str]] = {}
                self.executor = ThreadPoolExecutor(thread_name_prefix='UDPServer')
                super().__init__(server_address, request_handler)

            def shutdown(self) -> None:
                super().shutdown()
                for server_name, queue in self.message_queue.items():
                    queue.join()
                    queue.put('')
                self.executor.shutdown(wait=True)

        host = self.config['BOT']['HOST']
        port = int(self.config['BOT']['PORT'])
        self.udp_server = MyThreadingUDPServer((host, port), RequestHandler)
        self.executor.submit(self.udp_server.serve_forever)
        self.log.debug('- Listener started on interface {} port {} accepting commands.'.format(host, port))
