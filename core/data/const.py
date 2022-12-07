from enum import Enum


class Side(Enum):
    UNKNOWN = -1
    SPECTATOR = 0
    RED = 1
    BLUE = 2
    NEUTRAL = 3


class Status(Enum):
    UNREGISTERED = 'Unregistered'
    SHUTDOWN = 'Shutdown'
    RUNNING = 'Running'
    PAUSED = 'Paused'
    STOPPED = 'Stopped'
    LOADING = 'Loading'


class Channel(Enum):
    STATUS = 'STATUS_CHANNEL'
    ADMIN = 'ADMIN_CHANNEL'
    CHAT = 'CHAT_CHANNEL'
