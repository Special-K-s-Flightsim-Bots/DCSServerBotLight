from __future__ import annotations
from abc import ABC, abstractmethod
from core import utils
from core.report.env import ReportEnv
from core.report.errors import TooManyElements
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core import DCSServerBot


class ReportElement(ABC):
    def __init__(self, env: ReportEnv):
        self.env = env
        self.bot: DCSServerBot = env.bot
        self.log = env.bot.log

    @abstractmethod
    def render(self, **kwargs):
        pass


class EmbedElement(ReportElement):
    def __init__(self, env: ReportEnv):
        super().__init__(env)
        self.embed = env.embed

    def add_field(self, *, name, value, inline=True):
        return self.embed.add_field(name=name[:256] or '_ _',
                                    value=(value[:1024] if isinstance(value, str) else value) or '_ _',
                                    inline=inline)

    def set_image(self, *, url):
        return self.embed.set_image(url=url)

    @abstractmethod
    def render(self, **kwargs):
        pass


class Image(EmbedElement):
    def render(self, url: str):
        self.set_image(url=url)


class Ruler(EmbedElement):
    def render(self, ruler_length: Optional[int] = 34):
        self.add_field(name='▬' * ruler_length, value='_ _', inline=False)


class Field(EmbedElement):
    def render(self, name: str, value: Any, inline: Optional[bool] = True):
        self.add_field(name=utils.format_string(name, '_ _', **self.env.params),
                       value=utils.format_string(value, '_ _', **self.env.params), inline=inline)


class Table(EmbedElement):
    def render(self, values: dict, inline: Optional[bool] = True):
        header = None
        cols = ['', '', '']
        elements = 0
        for row in values:
            elements = len(row)
            if elements > 3:
                raise TooManyElements(elements)
            if not header:
                header = list(row.keys())
            for i in range(0, elements):
                cols[i] += utils.format_string(row[header[i]], '_ _', **self.env.params) + '\n'
        for i in range(0, elements):
            self.add_field(name=header[i], value=cols[i], inline=inline)
        if inline:
            for i in range(elements, 3):
                self.add_field(name='_ _', value='_ _')
