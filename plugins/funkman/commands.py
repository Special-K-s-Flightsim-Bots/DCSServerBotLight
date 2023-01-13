import json
import os
from configparser import ConfigParser
from core import Plugin, DCSServerBot, PluginInstallationError, PluginConfigurationError
from .listener import FunkManEventListener


class FunkMan(Plugin):

    def install(self):
        if not self.locals:
            raise PluginInstallationError(self.plugin_name, "Can't find config/funkman.json, please create one!")
        config = self.locals['configs'][0]
        if 'install' not in config:
            raise PluginConfigurationError(self.plugin_name, 'install')
        if not os.path.exists(config['install']):
            raise FileNotFoundError(config['install'])
        self.log.debug('  => Checking for FunkMan.ini ...')
        if os.path.exists(config['install'] + os.path.sep + 'FunkMan.ini'):
            self.log.debug('  => Migrating FunkMan.ini ...')
            ini = ConfigParser()
            ini.read(config['install'] + os.path.sep + 'FunkMan.ini')
            if 'CHANNELID_MAIN' in ini['FUNKBOT']:
                config['CHANNELID_MAIN'] = ini['FUNKBOT']['CHANNELID_MAIN']
            if 'CHANNELID_RANGE' in ini['FUNKBOT']:
                config['CHANNELID_RANGE'] = ini['FUNKBOT']['CHANNELID_RANGE']
            if 'CHANNELID_AIRBOSS' in ini['FUNKBOT']:
                config['CHANNELID_AIRBOSS'] = ini['FUNKBOT']['CHANNELID_AIRBOSS']
            if 'IMAGEPATH' in ini['FUNKPLOT']:
                if ini['FUNKPLOT']['IMAGEPATH'].startswith('.'):
                    config['IMAGEPATH'] = config['install'] + ini['FUNKPLOT']['IMAGEPATH'][1:]
                else:
                    config['IMAGEPATH'] = ini['FUNKPLOT']['IMAGEPATH']
            with open('config/funkman.json', 'w') as outfile:
                json.dump(self.locals, outfile, indent=2)
        else:
            self.log.debug('  => No FunkMan.ini found.')
        super().install()


async def setup(bot: DCSServerBot):
    await bot.add_cog(FunkMan(bot, FunkManEventListener))
