import discord
from core import report, Server


class Header(report.EmbedElement):
    def render(self, mission_info: dict, server_name: str, message: discord.Message):
        server: Server = self.bot.servers[server_name]


class Body(report.EmbedElement):
    def render(self, mission_info: dict, server_name: str, message: discord.Message):
        server: Server = self.bot.servers[server_name]
        self.embed.add_field(name='Blue Tasks', value=mission_info['briefing']['descriptionBlueTask'][:1024].strip('\n') or 'n/a', inline=False)
        self.embed.add_field(name='Red Tasks', value=mission_info['briefing']['descriptionRedTask'][:1024].strip('\n') or 'n/a', inline=False)
