from __future__ import annotations
import discord
from core import EventListener, Channel
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core import Server


class GameMasterEventListener(EventListener):

    async def onChatMessage(self, data) -> None:
        server: Server = self.bot.servers[data['server_name']]
        chat_channel: Optional[discord.TextChannel] = server.get_channel(Channel.CHAT)
        if chat_channel:
            if 'from_id' in data and data['from_id'] != 1 and len(data['message']) > 0:
                await chat_channel.send(data['from_name'] + ': ' + data['message'])
