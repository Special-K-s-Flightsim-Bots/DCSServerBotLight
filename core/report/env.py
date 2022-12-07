from __future__ import annotations
import discord
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import DCSServerBot


@dataclass
class ReportEnv:
    bot: DCSServerBot
    embed: discord.Embed = None
    filename: str = None
    params: dict = None
