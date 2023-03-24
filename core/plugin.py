from __future__ import annotations
import json
import os
import sys
from copy import deepcopy
from core import DBConnection
from discord.ext import commands
from os import path
from shutil import copytree
from typing import Type, Optional, TYPE_CHECKING
from .listener import TEventListener

if TYPE_CHECKING:
    from core import DCSServerBot, Server


class Plugin(commands.Cog):

    def __init__(self, bot: DCSServerBot, eventlistener: Type[TEventListener] = None):
        self.plugin_name = type(self).__module__.split('.')[-2]
        self.plugin_version = getattr(sys.modules['plugins.' + self.plugin_name], '__version__')
        self.bot: DCSServerBot = bot
        self.log = bot.log
        self.loop = bot.loop
        self.locals = self.read_locals()
        self._config = dict[str, dict]()
        self.eventlistener: Type[TEventListener] = eventlistener(self) if eventlistener else None

    async def cog_load(self) -> None:
        await self.install()
        if self.eventlistener:
            self.bot.register_eventListener(self.eventlistener)
        self.log.info(f'  => {self.plugin_name.title()} loaded.')

    async def cog_unload(self):
        if self.eventlistener:
            await self.eventlistener.shutdown()
            self.bot.unregister_eventListener(self.eventlistener)
        # delete a possible configuration
        self._config.clear()
        self.log.info(f'  => {self.plugin_name.title()} unloaded.')

    async def install(self):
        self.init_db()
        for server in self.bot.servers.values():
            source_path = f'./plugins/{self.plugin_name}/lua'
            if path.exists(source_path):
                target_path = path.expandvars(self.bot.config[server.installation]['DCS_HOME'] +
                                              f'\\Scripts\\net\\DCSServerBot\\{self.plugin_name}\\')
                copytree(source_path, target_path, dirs_exist_ok=True)
                self.log.debug(f'  => Luas installed into {server.installation}')
        # create report directories for convenience
        source_path = f'./plugins/{self.plugin_name}/reports'
        if path.exists(source_path):
            target_path = f'./reports/{self.plugin_name}'
            if not path.exists(target_path):
                os.makedirs(target_path)

    def migrate(self, version: str) -> None:
        pass

    async def before_dcs_update(self) -> None:
        pass

    async def after_dcs_update(self) -> None:
        pass

    def init_db(self):
        with DBConnection() as cursor:
            cursor.execute('SELECT version FROM plugins WHERE plugin = ?', (self.plugin_name,))
            row = cursor.fetchone()
            # first installation
            if not row:
                tables_file = f'./plugins/{self.plugin_name}/db/tables.sql'
                if path.exists(tables_file):
                    with open(tables_file) as tables_sql:
                        for query in tables_sql.readlines():
                            self.log.debug(query.rstrip())
                            cursor.execute(query.rstrip())
                cursor.execute('INSERT INTO plugins (plugin, version) VALUES (?, ?) ON CONFLICT (plugin) DO NOTHING',
                               (self.plugin_name, self.plugin_version))
                self.log.info(f'  => {self.plugin_name.title()} installed.')
            else:
                installed = row[0]
                # old variant, to be migrated
                if installed.startswith('v'):
                    installed = installed[1:]
                while installed != self.plugin_version:
                    updates_file = f'./plugins/{self.plugin_name}/db/update_v{installed}.sql'
                    if path.exists(updates_file):
                        with open(updates_file) as updates_sql:
                            for query in updates_sql.readlines():
                                self.log.debug(query.rstrip())
                                cursor.execute(query.rstrip())
                    ver, rev = installed.split('.')
                    installed = ver + '.' + str(int(rev) + 1)
                    self.migrate(installed)
                    self.log.info(f'  => {self.plugin_name.title()} migrated to version {installed}.')
                    cursor.execute('UPDATE plugins SET version = ? WHERE plugin = ?',
                                   (installed, self.plugin_name))

    def read_locals(self) -> dict:
        if path.exists(f'./config/{self.plugin_name}.json'):
            filename = f'./config/{self.plugin_name}.json'
        elif path.exists(f'./plugins/{self.plugin_name}/config/config.json'):
            filename = f'./plugins/{self.plugin_name}/config/config.json'
        else:
            return {}
        self.log.debug(f'  => Reading plugin configuration from {filename} ...')
        with open(filename, encoding='utf-8') as file:
            return json.load(file)

    def get_config(self, server: Server) -> Optional[dict]:
        if server.name not in self._config:
            if 'configs' in self.locals:
                specific = default = None
                for element in self.locals['configs']:
                    if 'installation' in element or 'server_name' in element:
                        if ('installation' in element and server.installation == element['installation']) or \
                                ('server_name' in element and server.name == element['server_name']):
                            specific = deepcopy(element)
                    else:
                        default = deepcopy(element)
                if default and not specific:
                    self._config[server.name] = default
                elif specific and not default:
                    self._config[server.name] = specific
                elif default and specific:
                    self._config[server.name] = default | specific
            else:
                return None
        return self._config[server.name] if server.name in self._config else None

    def rename(self, old_name: str, new_name: str) -> None:
        # this function has to be implemented in your own plugins, if a server rename takes place
        pass


class PluginRequiredError(Exception):
    def __init__(self, plugin: str):
        super().__init__(f'Required plugin "{plugin.title()}" is missing!')


class PluginConflictError(Exception):
    def __init__(self, plugin1: str, plugin2: str):
        super().__init__(f'Plugin "{plugin1.title()}" conflicts with plugin "{plugin2.title()}"!')


class PluginConfigurationError(Exception):
    def __init__(self, plugin: str, option: str):
        super().__init__(f'Option "{option}" missing in {plugin}.json!')


class PluginInstallationError(Exception):
    def __init__(self, plugin: str, reason: str):
        super().__init__(f'Plugin "{plugin.title()}" could not be installed: {reason}')
