from __future__ import annotations
import asyncio
import discord
import inspect
import json
import os
import sys
from abc import ABC, abstractmethod
from contextlib import suppress
from discord.ext.commands import Context
from os import path
from typing import List, Tuple, Optional, TYPE_CHECKING, Any, cast, Union
from . import ReportEnv, parse_params, parse_input, utils, UnknownReportElement, ReportElement, ClassNotFound, \
    ValueNotInRange, ReportException
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
                                element_class.render(**render_args)
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

        async def pagination(index=0):
            try:
                message = None
                try:
                    kwargs[name] = values[index]
                    env = await func(*args, **kwargs)
                    file = discord.File(env.filename, filename=os.path.basename(env.filename)) if env.filename else None
                    with suppress(Exception):
                        message = await self.ctx.send(embed=env.embed, file=file, delete_after=self.timeout)
                    if env.filename:
                        os.remove(env.filename)
                        env.filename = None
                except ValueNotInRange as ex:
                    await self.ctx.send(str(ex))
                except Exception as ex:
                    self.log.exception(ex)
                    await self.ctx.send('An error occurred. Please contact your Admin.')

                if message and (len(values) > 1):
                    await message.add_reaction('◀️')
                    await message.add_reaction('⏹️')
                    await message.add_reaction('▶️')
                    react = await utils.wait_for_single_reaction(self.bot, self.ctx, message)
                    if react.emoji == '◀️':
                        await message.delete()
                        await pagination((index - 1) if index > 0 else len(values) - 1)
                    elif react.emoji == '⏹️':
                        raise asyncio.TimeoutError
                    elif react.emoji == '▶️':
                        await message.delete()
                        await pagination((index + 1) if index < (len(values) - 1) else 0)
            except asyncio.TimeoutError:
                if isinstance(self.ctx, discord.DMChannel):
                    await message.delete()
                else:
                    await message.clear_reactions()

        await pagination(start_index)
        return self.env


class PersistentReport(Report):

    def __init__(self, bot: DCSServerBot, plugin: str, filename: str, server: Server, embed_name: str,
                 channel_id: Optional[Union[Channel, int]] = Channel.STATUS):
        super().__init__(bot, plugin, filename)
        self.server = server
        self.embed_name = embed_name
        self.channel_id = channel_id

    async def render(self, *args, **kwargs) -> ReportEnv:
        try:
            env = await super().render(*args, **kwargs)
            file = discord.File(env.filename, filename=os.path.basename(env.filename)) if env.filename else None
            self.bot.loop.call_soon(asyncio.create_task, self.server.setEmbed(self.embed_name, env.embed, file,
                                                                              channel_id=self.channel_id))
            return env
        except ReportException as ex:
            self.log.exception(ex)
