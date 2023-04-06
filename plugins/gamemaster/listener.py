from __future__ import annotations
import discord
import logging
import os
from core import EventListener, Channel, event
from logging.handlers import RotatingFileHandler
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core import Player, Server, Plugin


class GameMasterEventListener(EventListener):

    def __init__(self, plugin: Plugin):
        super().__init__(plugin)
        self.chat_log = dict()

    @event(name="registerDCSServer")
    async def registerDCSServer(self, server: Server, data: dict) -> None:
        if self.bot.config.getboolean(server.installation, 'CHAT_LOG') and server.installation not in self.chat_log:
            self.chat_log[server.installation] = logging.getLogger(name=f'chat-{server.installation}')
            self.chat_log[server.installation].setLevel(logging.INFO)
            formatter = logging.Formatter(fmt=u'%(asctime)s.%(msecs)03d %(levelname)s\t%(message)s',
                                          datefmt='%Y-%m-%d %H:%M:%S')
            filename = os.path.expandvars(self.bot.config[server.installation]['DCS_HOME'] + r'\Logs\chat.log')
            fh = RotatingFileHandler(filename, encoding='utf-8',
                                     maxBytes=int(self.bot.config[server.installation]['CHAT_LOGROTATE_SIZE']),
                                     backupCount=int(self.bot.config[server.installation]['CHAT_LOGROTATE_COUNT']))
            fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            self.chat_log[server.installation].addHandler(fh)

    @event(name="onChatMessage")
    async def onChatMessage(self, server: Server, data: dict) -> None:
        player: Player = server.get_player(id=data['from_id'])
        if self.bot.config.getboolean(server.installation, 'CHAT_LOG'):
            self.chat_log[server.installation].info(f"{player.ucid}\t{player.name}\t{data['to']}\t{data['message']}")
        chat_channel: Optional[discord.TextChannel] = server.get_channel(Channel.CHAT)
        if chat_channel:
            if 'from_id' in data and data['from_id'] != 1 and len(data['message']) > 0:
                await chat_channel.send(data['from_name'] + ': ' + data['message'])
