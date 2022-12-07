# noinspection PyPackageRequirements
import aiohttp
import asyncio
import os
import shutil
from core import Plugin, DCSServerBot, utils, TEventListener, Status
from discord.ext import commands, tasks
from typing import Type, Any
from .listener import CloudListener


class CloudHandler(Plugin):

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
        self.cloud_bans.start()

    async def cog_unload(self):
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
            for ban in (await self.get('bans')):
                for server in self.bot.servers.values():
                    if server.status in [Status.RUNNING, Status.PAUSED, Status.STOPPED]:
                        server.sendtoDCS({
                            "command": "ban",
                            "ucid": ban["ucid"],
                            "reason": ban["reason"]
                        })
        except aiohttp.ClientError:
            self.log.error('- Cloud service not responding.')


async def setup(bot: DCSServerBot):
    if not os.path.exists('config/cloud.json'):
        bot.log.info('No cloud.json found, copying the sample.')
        shutil.copyfile('config/cloud.json.sample', 'config/cloud.json')
    await bot.add_cog(CloudHandler(bot, CloudListener))
