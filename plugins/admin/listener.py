import discord
from core import EventListener, Player, Server, Channel, chat_command


class AdminEventListener(EventListener):

    async def ban(self, data):
        for server in self.bot.servers.values():
            server.sendtoDCS({
                "command": "ban",
                "ucid": data['ucid'],
                "period": data['period'] if 'period' in data else 365*86400,
                "reason": data['reason']
            })

    @chat_command(name="911", usage="<message>", help="send an alert to admins (misuse will be punished!)")
    async def call911(self, server: Server, player: Player, params: list[str]):
        mentions = ''
        for role_name in [x.strip() for x in self.bot.config['ROLES']['DCS Admin'].split(',')]:
            role: discord.Role = discord.utils.get(self.bot.guilds[0].roles, name=role_name)
            if role:
                mentions += role.mention
        message = ' '.join(params)
        await server.get_channel(Channel.ADMIN).send(mentions +
                                                     f" 911 call from player {player.name} (ucid={player.ucid}):"
                                                     f"```{message}```")
