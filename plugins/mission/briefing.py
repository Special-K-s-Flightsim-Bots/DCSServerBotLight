import discord
from core import report


class Header(report.EmbedElement):
    def render(self, mission_info: dict, server_name: str, message: discord.Message):
        pass


class Body(report.EmbedElement):
    def render(self, mission_info: dict, server_name: str, message: discord.Message):
        self.embed.add_field(name='Blue Tasks', value=mission_info['briefing']['descriptionBlueTask'][:1024].strip('\n') or 'n/a', inline=False)
        self.embed.add_field(name='Red Tasks', value=mission_info['briefing']['descriptionRedTask'][:1024].strip('\n') or 'n/a', inline=False)
