from __future__ import annotations
from core import utils
from core.data.dataobject import DataObject, DataObjectFactory
from core.data.const import Side
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .server import Server


@dataclass
@DataObjectFactory.register("Player")
class Player(DataObject):
    server: Server = field(compare=False)
    id: int = field(compare=False)
    name: str = field(compare=False)
    active: bool = field(compare=False)
    side: Side = field(compare=False)
    ucid: str
    banned: bool = field(compare=False)
    slot: int = field(compare=False, default=0)
    sub_slot: int = field(compare=False, default=0)
    unit_callsign: str = field(compare=False, default='')
    unit_name: str = field(compare=False, default='')
    unit_display_name: str = field(compare=False, default='')
    unit_type: str = field(compare=False, default='')
    group_id: int = field(compare=False, default=0)
    group_name: str = field(compare=False, default='')

    def __post_init__(self):
        super().__post_init__()
        if self.id == 1:
            self.active = False
            return

    def is_active(self) -> bool:
        return self.active

    def is_multicrew(self) -> bool:
        return self.sub_slot != 0

    def is_banned(self) -> bool:
        return self.banned

    @property
    def display_name(self) -> str:
        return utils.escape_string(self.name)

    def update(self, data: dict):
        if 'id' in data:
            # if the ID has changed (due to reconnect), we need to update the server list
            if self.id != data['id']:
                del self.server.players[self.id]
                self.server.players[data['id']] = self
                self.id = data['id']
        if 'active' in data:
            self.active = data['active']
        if 'name' in data and self.name != data['name']:
            self.name = data['name']
        if 'side' in data:
            self.side = Side(data['side'])
        if 'slot' in data:
            self.slot = int(data['slot'])
        if 'sub_slot' in data:
            self.sub_slot = data['sub_slot']
        if 'unit_callsign' in data:
            self.unit_callsign = data['unit_callsign']
        if 'unit_name' in data:
            self.unit_name = data['unit_name']
        if 'unit_type' in data:
            self.unit_type = data['unit_type']
        if 'group_name' in data:
            self.group_name = data['group_name']
        if 'group_id' in data:
            self.group_id = data['group_id']
        if 'unit_display_name' in data:
            self.unit_display_name = data['unit_display_name']

    def sendChatMessage(self, message: str, sender: str = None):
        self.server.sendtoDCS({
            "command": "sendChatMessage",
            "to": self.id,
            "from": sender,
            "message": message
        })

    def sendUserMessage(self, message: str, timeout: Optional[int] = -1):
        if self.slot <= 0:
            [self.sendChatMessage(msg) for msg in message.splitlines()]
        else:
            self.sendPopupMessage(message, timeout)

    def sendPopupMessage(self, message: str, timeout: Optional[int] = -1, sender: str = None):
        if timeout == -1:
            timeout = self.bot.config['BOT']['MESSAGE_TIMEOUT']
        self.server.sendtoDCS({
            "command": "sendPopupMessage",
            "to": self.unit_name,
            "from": sender,
            "message": message,
            "time": timeout
        })

    def playSound(self, sound: str):
        self.server.sendtoDCS({
            "command": "playSound",
            "to": self.unit_name,
            "sound": sound
        })
