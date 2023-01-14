from __future__ import annotations
import discord
from dataclasses import dataclass
from discord import Embed
from discord.ui import View
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import DCSServerBot


@dataclass
class ReportEnv:
    bot: DCSServerBot
    embed: Embed = None
    view: View = None
    filename: str = None
    params: dict = None
