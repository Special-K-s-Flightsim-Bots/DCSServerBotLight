import os
import discord
import sys
import uuid
import matplotlib.figure
from core import EventListener, Plugin, Server
from matplotlib import pyplot as plt


class FunkManEventListener(EventListener):

    def __init__(self, plugin: Plugin):
        super().__init__(plugin)
        self.config = self.locals['configs'][0]
        sys.path.append(self.config['install'])
        from funkman.funkplot.funkplot import FunkPlot
        from funkman.utils.utils import _GetVal
        self.funkplot = FunkPlot(ImagePath=self.config['IMAGEPATH'])
        self._GetVal = _GetVal

    # from FunkBot, to be replaced with a proper function call!
    def _create_lso_embed(self, result: dict) -> discord.Embed:
        actype = self._GetVal(result, "airframe", "Unkown")
        Tgroove = self._GetVal(result, "Tgroove", "?", 1)
        player = self._GetVal(result, "name", "Ghostrider")
        grade = self._GetVal(result, "grade", "?")
        points = self._GetVal(result, "points", "?")
        details = self._GetVal(result, "details", "?")
        case = self._GetVal(result, "case", "?")
        wire = self._GetVal(result, "wire", "?")
        carriertype = self._GetVal(result, "carriertype", "?")
        carriername = self._GetVal(result, "carriername", "?")
        windondeck = self._GetVal(result, "wind", "?", 1)
        missiontime = self._GetVal(result, "mitime", "?")
        missiondate = self._GetVal(result, "midate", "?")
        theatre = self._GetVal(result, "theatre", "Unknown Map")
        theta = self._GetVal(result, "carrierrwy", -9)

        color = 0x00ff00
        urlIm = "https://i.imgur.com/1bWgcV7.png"
        if type(points) != str:
            if points == 0:
                color = 0x000000  # black
                urlIm = "https://i.imgur.com/rZpu9c0.png"
            elif points == 1:
                color = 0xff0000  # red
                urlIm = "https://i.imgur.com/LXgD2Op.png"
            elif points == 2:
                color = 0xFFA500  # orange
                urlIm = "https://i.imgur.com/EjviMBk.png"
            elif points == 2.5:
                color = 0xB47E59  # brown
                urlIm = "https://i.imgur.com/nYWrL4Z.png"
            elif points == 3:
                color = 0xFFFF00  # yellow
                urlIm = "https://i.imgur.com/wH0Gjqx.png"
            elif points == 4:
                color = 0x00FF00  # green
                urlIm = "https://i.imgur.com/1bWgcV7.png"
            elif points == 5:
                color = 0x0000FF  # blue
                urlIm = "https://i.imgur.com/6ecFSqo.png"

        # Create Embed
        embed = discord.Embed(title="LSO Grade",
                              description=f"Result for {player} at carrier {carriername} [{carriertype}]",
                              color=color)

        # Images.
        embed.set_thumbnail(url=urlIm)

        # Data.
        embed.add_field(name="Grade", value=grade)
        embed.add_field(name="Points", value=points)
        embed.add_field(name="Details", value=details)
        embed.add_field(name="Groove", value=Tgroove)
        if wire != "?":
            embed.add_field(name="Wire", value=wire)
        embed.add_field(name="Case", value=case)
        embed.add_field(name="Wind", value=windondeck)
        embed.add_field(name="Aircraft", value=actype)

        # Footer.
        embed.set_footer(text=f"{theatre}: {missiondate} ({missiontime})")
        return embed

    @staticmethod
    def _save_fig(fig: matplotlib.figure.Figure) -> str:
        filename = f'{uuid.uuid4()}.png'
        fig.savefig(filename, bbox_inches='tight', facecolor='#2C2F33')
        plt.close(fig)
        return filename

    async def _send_fig(self, server: Server, fig: matplotlib.figure.Figure, channel: str):
        filename = self._save_fig(fig)
        try:
            config = self.plugin.get_config(server)
            channel = self.bot.get_channel(int(config[channel]))
            await channel.send(file=discord.File(filename))
        finally:
            if os.path.exists(filename):
                os.remove(filename)

    async def moose_text(self, data: dict):
        server: Server = self.bot.servers[data['server_name']]
        config = self.plugin.get_config(server)
        channel = self.bot.get_channel(int(config['CHANNELID_MAIN']))
        await channel.send(data['text'])

    async def moose_bomb_result(self, data: dict):
        server: Server = self.bot.servers[data['server_name']]
        fig, _ = self.funkplot.PlotBombRun(data)
        await self._send_fig(server, fig, 'CHANNELID_RANGE')

    async def moose_strafe_result(self, data: dict):
        server: Server = self.bot.servers[data['server_name']]
        fig, _ = self.funkplot.PlotStrafeRun(data)
        await self._send_fig(server, fig, 'CHANNELID_RANGE')

    async def moose_lso_grade(self, data: dict):
        embed = self._create_lso_embed(data)
        fig, _ = self.funkplot.PlotTrapSheet(data)
        filename = self._save_fig(fig)
        try:
            embed.set_image(url=f"attachment://{filename}")
            server: Server = self.bot.servers[data['server_name']]
            config = self.plugin.get_config(server)
            channel = self.bot.get_channel(int(config['CHANNELID_AIRBOSS']))
            await channel.send(embed=embed, file=discord.File(filename))
        finally:
            if os.path.exists(filename):
                os.remove(filename)
