import aiohttp
from core import EventListener, Server, event


class CloudListener(EventListener):

    @event(name="registerDCSServer")
    async def registerDCSServer(self, server: Server, data: dict) -> None:
        # if the server is running, the bans will be sent by the plugin
        if 'sync-' not in data['channel']:
            server: Server = self.bot.servers[data['server_name']]
            try:
                for ban in (await self.plugin.get('bans')):
                    server.sendtoDCS({
                        "command": "ban",
                        "ucid": ban["ucid"],
                        "reason": ban["reason"]
                    })
            except aiohttp.ClientError:
                self.log.error('- Cloud service not responding.')
