# noinspection PyPackageRequirements
import aiohttp
import asyncio
import discord
import os
import shutil

from core import Plugin, DCSServerBot, utils, TEventListener, Status
from discord.ext import commands, tasks
from typing import Type, Any
from .listener import CloudListener


class CloudHandlerAgent(Plugin):

    def __init__(self, bot: DCSServerBot, eventlistener: Type[TEventListener] = None):
        super().__init__(bot, eventlistener)
        if not len(self.read_locals()):
            raise commands.ExtensionFailed(self.plugin_name, FileNotFoundError("No cloud.json available."))
        self.config = self.locals['configs'][0]
        headers = {
            "Content-type": "application/json"
        }
        if 'token' in self.config:
            headers['Authorization'] = f"Bearer {self.config['token']}"

        self.session = aiohttp.ClientSession(raise_for_status=True, headers=headers)
        self.base_url = f"{self.config['protocol']}://{self.config['host']}:{self.config['port']}"
        self.client = {
            "guild_id": self.bot.guilds[0].id,
            "guild_name": self.bot.guilds[0].name,
            "owner_id": self.bot.owner_id
        }
        if 'dcs-ban' not in self.config or self.config['dcs-ban']:
            self.cloud_bans.start()

    async def cog_unload(self):
        if 'dcs-ban' not in self.config or self.config['dcs-ban']:
            self.cloud_bans.cancel()
        asyncio.create_task(self.session.close())
        await super().cog_unload()

    async def get(self, request: str) -> Any:
        url = f"{self.base_url}/{request}"
        async with self.session.get(url) as response:  # type: aiohttp.ClientResponse
            return await response.json()

    async def post(self, request: str, data: Any) -> Any:
        async def send(element):
            url = f"{self.base_url}/{request}/"
            async with self.session.post(url, json=element) as response:  # type: aiohttp.ClientResponse
                return await response.json()

        if isinstance(data, list):
            for line in data:
                await send(line)
        else:
            await send(data)

    @commands.command(description='Checks the connection to the DCSServerBot cloud')
    @utils.has_role('Admin')
    @commands.guild_only()
    async def cloud(self, ctx):
        message = await ctx.send('Checking cloud connection ...')
        try:
            await self.get('verify')
            await ctx.send('Cloud connection established.')
            return
        except aiohttp.ClientError:
            await ctx.send('Cloud not connected.')
        finally:
            await message.delete()

    @tasks.loop(minutes=15.0)
    async def cloud_bans(self):
        try:
            bans = await self.get('bans')
            for server in self.bot.servers.values():
                if server.status in [Status.RUNNING, Status.PAUSED, Status.STOPPED]:
                    for ban in bans:
                        server.sendtoDCS({
                            "command": "ban",
                            "ucid": ban["ucid"],
                            "reason": ban["reason"]
                        })
        except aiohttp.ClientError:
            self.log.error('- Cloud service not responding.')


class CloudHandlerMaster(CloudHandlerAgent):

    def __init__(self, bot: DCSServerBot, eventlistener: Type[TEventListener] = None):
        super().__init__(bot, eventlistener)
        if 'discord-ban' not in self.config or self.config['discord-ban']:
            self.master_bans.start()

    async def cog_unload(self):
        if 'discord-ban' not in self.config or self.config['discord-ban']:
            self.master_bans.cancel()
        await super().cog_unload()
        
    @tasks.loop(minutes=15.0)
    async def master_bans(self):
        try:
            for ban in (await self.get('discord-bans')):
                user: discord.User = await self.bot.fetch_user(ban['discord_id'])
                await self.bot.guilds[0].ban(user, reason='DGSA: ' + ban['reason'])
        except aiohttp.ClientError:
            self.log.error('- Cloud service not responding.')
        except discord.Forbidden:
            self.log.warn('- DCSServerBot does not have the permission to ban users.')


async def setup(bot: DCSServerBot):
    if not os.path.exists('config/cloud.json'):
        bot.log.info('No cloud.json found, copying the sample.')
        shutil.copyfile('config/cloud.json.sample', 'config/cloud.json')
    if bot.config.getboolean('BOT', 'MASTER') is True:
        await bot.add_cog(CloudHandlerMaster(bot, CloudListener))
    else:
        await bot.add_cog(CloudHandlerAgent(bot, CloudListener))
