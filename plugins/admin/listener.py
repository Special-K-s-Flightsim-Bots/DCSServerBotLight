import asyncio
import discord
from core import EventListener, Player, Server, Channel


class AdminEventListener(EventListener):

    async def ban(self, data):
        for server in self.bot.servers.values():
            server.sendtoDCS({
                "command": "ban",
                "ucid": data['ucid'],
                "period": data['period'] if 'period' in data else 365*86400,
                "reason": data['reason']
            })

    async def onChatCommand(self, data: dict) -> None:
        server: Server = self.bot.servers[data['server_name']]
        player: Player = server.get_player(id=data['from_id'], active=True)
        if not player:
            return
        if data['subcommand'] == '911':
            mentions = ''
            for role_name in [x.strip() for x in self.bot.config['ROLES']['DCS Admin'].split(',')]:
                role: discord.Role = discord.utils.get(self.bot.guilds[0].roles, name=role_name)
                if role:
                    mentions += role.mention
            message = ' '.join(data['params'])
            self.bot.loop.call_soon(asyncio.create_task, server.get_channel(Channel.ADMIN).send(
                mentions + f" 911 call from player {player.name} (ucid={player.ucid}):```{message}```"))
