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
            bans: list[dict] = await self.get('discord-bans')
            users_to_ban = [await self.bot.fetch_user(x['discord_id']) for x in bans]
            guild = self.bot.guilds[0]
            guild_bans = [entry async for entry in guild.bans()]
            banned_users = [x.user for x in guild_bans if x.reason.startswith('DGSA:')]
            # unban users that should not be banned anymore
            for user in [x for x in banned_users if x not in users_to_ban]:
                await guild.unban(user, reason='DGSA: ban revoked.')
            # ban users that were not banned yet
            for user in [x for x in users_to_ban if x not in banned_users]:
                if user.id == self.bot.owner_id:
                    continue
                reason = next(x['reason'] for x in bans if x['discord_id'] == user.id)
                await guild.ban(user, reason='DGSA: ' + reason)
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
