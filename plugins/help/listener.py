from __future__ import annotations
from core import EventListener
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Server, Player


class HelpListener(EventListener):
    async def onChatCommand(self, data: dict) -> None:
        server: Server = self.bot.servers[data['server_name']]
        prefix = self.bot.config['BOT']['CHAT_COMMAND_PREFIX']
        if data['subcommand'] == 'help':
            player = server.get_player(id=data['from_id'], active=True)
            if not player:
                return
            messages = [
                f'You can use the following commands:\n',
                f'"{prefix}atis airport" display ATIS information',
                f'"{prefix}911 <text>"   send an alert to admins (misuse will be punished!)'
            ]
            player.sendUserMessage('\n'.join(messages), 30)

    async def onPlayerStart(self, data: dict) -> None:
        if data['id'] == 1:
            return
        server: Server = self.bot.servers[data['server_name']]
        player: Player = server.get_player(id=data['id'])
        prefix = self.bot.config['BOT']['CHAT_COMMAND_PREFIX']
        player.sendChatMessage(f'Use "{prefix}help" for commands.')
