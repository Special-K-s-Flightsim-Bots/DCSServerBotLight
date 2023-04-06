from __future__ import annotations
import asyncio
import discord
import inspect
import json
import os
import sys
from abc import ABC, abstractmethod
from discord import Interaction, SelectOption
from discord.ext.commands import Context
from discord.ui import View, Button, Select, Item
from os import path
from typing import List, Tuple, Optional, TYPE_CHECKING, Any, cast, Union

from . import ReportEnv, parse_params, parse_input, utils, UnknownReportElement, ReportElement, ClassNotFound
from ..data.const import Channel

if TYPE_CHECKING:
    from core import DCSServerBot, Server


class Report:

    def __init__(self, bot: DCSServerBot, plugin: str, filename: str):
        self.bot = bot
        self.log = bot.log
        self.env = ReportEnv(bot)
        default = f'./plugins/{plugin}/reports/{filename}'
        overwrite = f'./reports/{plugin}/{filename}'
        if path.exists(overwrite):
            filename = overwrite
        else:
            filename = default
        if not path.exists(filename):
            raise FileNotFoundError(filename)
        with open(filename, encoding='utf-8') as file:
            self.report_def = json.load(file)

    async def render(self, *args, **kwargs) -> ReportEnv:
        if 'input' in self.report_def:
            self.env.params = await parse_input(kwargs, self.report_def['input'])
        else:
            self.env.params = kwargs.copy()
        # add the bot to be able to access the whole environment from inside the report
        self.env.params['bot'] = self.bot
        # format the embed
        if 'color' in self.report_def:
            self.env.embed = discord.Embed(color=getattr(discord.Color, self.report_def['color'])())
        else:
            self.env.embed = discord.Embed()
        for name, item in self.report_def.items():
            # parse report parameters
            if name == 'title':
                self.env.embed.title = utils.format_string(item, **self.env.params)[:256]
            elif name == 'description':
                self.env.embed.description = utils.format_string(item, **self.env.params)[:4096]
            elif name == 'url':
                self.env.embed.url = item
            elif name == 'img':
                self.env.embed.set_thumbnail(url=item)
            elif name == 'footer':
                footer = self.env.embed.footer.text
                text = utils.format_string(item, **self.env.params)
                if footer is None:
                    footer = text
                else:
                    footer += '\n' + text
                self.env.embed.set_footer(text=footer[:2048])
            elif name == 'elements':
                for element in item:
                    if isinstance(element, dict):
                        if 'params' in element:
                            element_args = parse_params(self.env.params, element['params'])
                        else:
                            element_args = self.env.params.copy()
                        element_class = utils.str_to_class(element['class']) if 'class' in element else None
                        if not element_class and 'type' in element:
                            element_class = getattr(sys.modules['core.report.elements'], element['type'])
                    elif isinstance(element, str):
                        element_class = getattr(sys.modules['core.report.elements'], element)
                        element_args = self.env.params.copy()
                    else:
                        raise UnknownReportElement(str(element))
                    if element_class:
                        # remove parameters, that are not in the class __init__ signature
                        signature = inspect.signature(element_class.__init__).parameters.keys()
                        class_args = {name: value for name, value in element_args.items() if name in signature}
                        element_class = element_class(self.env, **class_args)
                        if isinstance(element_class, ReportElement):
                            # remove parameters, that are not in the render classes signature
                            signature = inspect.signature(element_class.render).parameters.keys()
                            render_args = {name: value for name, value in element_args.items() if name in signature}
                            try:
                                await asyncio.to_thread(element_class.render, **render_args)
                            except Exception as ex:
                                self.log.exception(ex)
                        else:
                            raise UnknownReportElement(element['class'])
                    else:
                        raise ClassNotFound(element['class'])
        return self.env


class Pagination(ABC):
    def __init__(self, env: ReportEnv):
        self.env = env

    @abstractmethod
    def values(self, **kwargs) -> list[Any]:
        pass


class PaginationReport(Report):

    class NoPaginationInformation(Exception):
        pass

    def __init__(self, bot: DCSServerBot, ctx: Union[Context, discord.DMChannel], plugin: str, filename: str,
                 timeout: Optional[int] = None, pagination: Optional[list] = None):
        super().__init__(bot, plugin, filename)
        self.ctx = ctx
        self.timeout = timeout
        self.pagination = pagination
        if 'pagination' not in self.report_def:
            raise PaginationReport.NoPaginationInformation

    def read_param(self, param: dict, **kwargs) -> Tuple[str, List]:
        name = param['name']
        values = None
        if 'values' in param:
            values = param['values']
        elif 'obj' in param:
            obj = kwargs[param['obj']]
            if isinstance(obj, list):
                values = obj
            elif isinstance(obj, dict):
                values = obj.keys()
        elif 'class' in param:
            values = cast(Pagination, utils.str_to_class(param['class'])(self.env)).values(**kwargs)
        elif self.pagination:
            values = self.pagination
        return name, values

    class PaginationReportView(View):
        def __init__(self, name, values, index, func, *args, **kwargs):
            super().__init__()
            self.name = name
            self.values = values
            self.index = index
            self.func = func
            self.args = args
            self.kwargs = kwargs
            select: Select = cast(Select, self.children[0])
            self.formatter = kwargs.get('formatter')
            if self.formatter:
                select.options = [SelectOption(label=self.formatter(x) or 'All',
                                               value=str(idx)) for idx, x in enumerate(self.values)]
            else:
                select.options = [SelectOption(label=x or 'All',
                                               value=str(idx)) for idx, x in enumerate(self.values)]
            if self.index == 0:
                self.children[1].disabled = True
                self.children[2].disabled = True
            if self.index == len(values) - 1:
                self.children[3].disabled = True
                self.children[4].disabled = True

        async def render(self, value) -> ReportEnv:
            self.kwargs[self.name] = value if value != 'All' else None
            return await self.func(*self.args, **self.kwargs)

        async def paginate(self, value, interaction: discord.Interaction):
            await interaction.response.defer()
            env = await self.render(value)
            try:
                if self.index == 0:
                    self.children[1].disabled = True
                    self.children[2].disabled = True
                    self.children[3].disabled = False
                    self.children[4].disabled = False
                elif self.index == len(self.values) - 1:
                    self.children[1].disabled = False
                    self.children[2].disabled = False
                    self.children[3].disabled = True
                    self.children[4].disabled = True
                else:
                    self.children[1].disabled = False
                    self.children[2].disabled = False
                    self.children[3].disabled = False
                    self.children[4].disabled = False
                if env.filename:
                    await interaction.edit_original_response(embed=env.embed, view=self, attachments=[
                            discord.File(env.filename, filename=os.path.basename(env.filename))
                        ]
                    )
                else:
                    await interaction.edit_original_response(embed=env.embed, view=self, attachments=[])
            finally:
                if env.filename and os.path.exists(env.filename):
                    os.remove(env.filename)
                    env.filename = None

        @discord.ui.select()
        async def callback(self, interaction: Interaction, select: Select):
            self.index = int(select.values[0])
            await self.paginate(self.values[self.index], interaction)

        @discord.ui.button(label="<<", style=discord.ButtonStyle.secondary)
        async def on_start(self, interaction: Interaction, button: Button):
            self.index = 0
            await self.paginate(self.values[self.index], interaction)

        @discord.ui.button(label="Back", style=discord.ButtonStyle.primary)
        async def on_left(self, interaction: Interaction, button: Button):
            self.index -= 1
            await self.paginate(self.values[self.index], interaction)

        @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
        async def on_right(self, interaction: Interaction, button: Button):
            self.index += 1
            await self.paginate(self.values[self.index], interaction)

        @discord.ui.button(label=">>", style=discord.ButtonStyle.secondary)
        async def on_end(self, interaction: Interaction, button: Button):
            self.index = len(self.values) - 1
            await self.paginate(self.values[self.index], interaction)

        @discord.ui.button(label="Quit", style=discord.ButtonStyle.red)
        async def on_cancel(self, interaction: Interaction, button: Button):
            await interaction.response.defer()
            self.stop()

        async def on_error(self, interaction: Interaction, error: Exception, item: Item[Any], /) -> None:
            print(error)
            self.stop()

    async def render(self, *args, **kwargs) -> ReportEnv:
        name, values = self.read_param(self.report_def['pagination']['param'], **kwargs)
        start_index = 0
        if 'start_index' in kwargs:
            start_index = kwargs['start_index']
        elif name in kwargs:
            if kwargs[name] in values:
                start_index = values.index(kwargs[name])
            elif kwargs[name] or len(values) != 1:
                values.insert(0, kwargs[name])
        elif len(values) == 0:
            values = [None]
        func = super().render

        message = None
        view = self.PaginationReportView(name, values, start_index, func, *args, **kwargs)
        env = await view.render(values[start_index])
        try:
            try:
                message = await self.ctx.send(
                    embed=env.embed,
                    view=view,
                    file=discord.File(env.filename,
                                      filename=os.path.basename(env.filename)) if env.filename else None)
            finally:
                if env.filename and os.path.exists(env.filename):
                    os.remove(env.filename)
                    env.filename = None
            await view.wait()
        except Exception as ex:
            self.log.exception(ex)
            raise
        finally:
            if message:
                await message.delete()
        return self.env


class PersistentReport(Report):

    def __init__(self, bot: DCSServerBot, plugin: str, filename: str, server: Server, embed_name: str,
                 channel_id: Optional[Union[Channel, int]] = Channel.STATUS):
        super().__init__(bot, plugin, filename)
        self.server = server
        self.embed_name = embed_name
        self.channel_id = channel_id

    async def render(self, *args, **kwargs) -> ReportEnv:
        env = None
        try:
            env = await super().render(*args, **kwargs)
            file = discord.File(env.filename, filename=os.path.basename(env.filename)) if env.filename else None
            await self.server.setEmbed(self.embed_name, env.embed, file, channel_id=self.channel_id)
            return env
        except Exception as ex:
            self.log.exception(ex)
        finally:
            if env and env.filename and os.path.exists(env.filename):
                os.remove(env.filename)
