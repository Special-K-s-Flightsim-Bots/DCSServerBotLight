# Welcome to DCSServerBot (Light)!
This is a simpler solution of the full-fledged [DCSServerBot](https://github.com/Special-K-s-Flightsim-Bots/DCSServerBot),
that supports server and mission administration, display of mission details and players and some other nice feathers
that you see below.</br>
DCSServerBotLight does not need a Postgres database, so it is much easier to install and setup than the original solution.
If you want to use statistics, point based credit systems, punishment and slotblocking, you might want to look into the
full solution instead.

This documentation will show you the main features, how to install and configure the bot. Please check out the linked
plugin descriptions for each plugin.

First let's see, what it can do for you (installation instructions below)!

---
## Plugins
DCSServerBot(Light) has a modular architecture with plugins that support specific Discord commands or allow events from 
connected DCS servers to be processed. It comes with a set of plugins already, but you can add your own, if you wish.

### General Administrative Commands
These commands can be used to administrate the bot itself.

| Command     | Parameter | Channel       | Role    | Description                                                                                                                                                                                                               |
|-------------|-----------|---------------|---------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| .reload     | [Plugin]  | all           | Admin   | Reloads one or all plugin(s) and their configurations from disk.                                                                                                                                                          |
| .upgrade    |           | all           | Admin   | Upgrades the bot to the latest available version (git needed, see below).                                                                                                                                                 |
| .rename     | newname   | admin-channel | Admin   | Renames a DCS server. DCSServerBot auto-detects server renaming, too.                                                                                                                                                     |

### List of supported Plugins
| Plugin        | Scope                                                                | Optional | Dependent on | Documentation                              |
|---------------|----------------------------------------------------------------------|----------|--------------|--------------------------------------------|
| Mission       | Handling of missions, compared to the WebGUI.                        | no       |              | [README](./plugins/mission/README.md)      |
| Admin         | Admin commands to manage your DCS server.                            | yes      |              | [README](./plugins/admin/README.md)        |
| Scheduler     | Autostart / -stop of servers or missions, change weather, etc.       | yes      | Mission      | [README](./plugins/scheduler/README.md)    |
| GameMaster    | Interaction with the running mission (inform users, set flags, etc). | yes      |              | [README](./plugins/gamemaster/README.md)   |
| Cloud         | Connection to the DGSA Global Ban System.                            | yes      |              | [README](./plugins/cloud/README.md)        |
| MOTD          | Generates a message of the day.                                      | yes      |              | [README](./plugins/motd/README.md)         |

### In case you want to write your own plugin ...
There is a sample in the plugins/samples subdirectory, that will guide you through the steps. If you want your plugin to be added to the distribution, just contact me via the contact details below.

## Extensions
Many DCS admins use extensions or add-ons like DCS-SRS, Taview, Lotatc, etc.</br>
DCSServerBot supports some of them already and can add a bit of quality of life. 
Check out [Extensions](./extensions/README.md) for more info on how to use them.

---
## Installation

### Prerequisites
You need to have at least [python 3.9](https://www.python.org/downloads/) installed. I have tested it with 3.9 only, 
newer versions might work but that's on your own risk. The python modules needed are listed in requirements.txt and 
can be installed with ```pip3 install -r requirements.txt```.</br>
For autoupdate to work, you have to install [GIT](https://git-scm.com/download/win) and make sure, ```git``` is in your 
PATH.

### Discord Token
The bot needs a unique Token per installation. This one can be obtained at http://discord.com/developers <br/>
Create a "New Application", add a Bot, select Bot from the left menu, give it a nice name and icon, press "Copy" below 
"Click to Reveal Token". Now your Token is in your clipboard. Paste it in dcsserverbot.ini in your config-directory.
Both "Privileged Gateway Intents" have to be enabled on that page.<br/>
To add the bot to your Discord guild, select "OAuth2" from the menu, then "URL Generator", select the "bot" checkbox, 
and then select the following permissions:</br>
* Manage Channels
* Send Messages
* Manage Messages
* Embed Links
* Attach Files
* Read Message History
* Add Reactions

Press "Copy" on the generated URL, paste it into the browser of your choice, select the guild the bot has to be added 
to - and you're done! For easier access to channel IDs, enable "Developer Mode" in "Advanced Settings" in Discord.

### Download
Best is to use ```git clone``` as you then can use the autoupdate functionality of the bot.<br/>
Otherwise download the latest release version and extract it somewhere on your PC that is running the DCS server(s) and 
give it write permissions, if needed. 

**Attention:** Make sure that the bot's installation directory can only be seen by yourself and is not exposed to anybody 
outside via www etc.

---
## Configuration
The bot configuration is held in **config/dcsserverbot.ini**. See **dcsserverbot.ini.sample** for an example.<br/>
If you start the bot for the first time, it will generate a basic file for you that you can amend to your needs afterwards.<br/>
For some configurations, default values may apply. They are kept in config/default.ini. **DO NOT CHANGE THIS FILE**, 
just overwrite the settings in your own dcsserverbot.ini, if you want to have them differently.

The following parameters can be used to configure the bot:

a) __BOT Section__

| Parameter           | Description                                                                                                                                                                                                                                                                                                                                                                                                          |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| OWNER               | The Discord ID of the Bot's owner (that's you!). If you don't know your ID, go to your Discord profile, make sure "Developer Mode" is enabled under "Advanced", go to "My Account", press the "..." besides your profile picture and select "Copy ID"                                                                                                                                                                |
| TOKEN               | The token to be used to run the bot. Can be obtained at http://discord.com/developers.                                                                                                                                                                                                                                                                                                                               |
| COMMAND_PREFIX      | The prefix to be used by Discord commands. Default is '.'                                                                                                                                                                                                                                                                                                                                                            |
| CHAT_COMMAND_PREFIX | The prefix to be used by ingame-chat comannds. Default is '-'                                                                                                                                                                                                                                                                                                                                                        |                                                                                                                                                                                                                                                                                                                                                        
| HOST                | IP the bot listens on for messages from DCS. Default is 127.0.0.1, to only accept internal communication on that machine.                                                                                                                                                                                                                                                                                            |
| PORT                | UDP port, the bot listens on for messages from DCS. Default is 10081. **__Don't expose this port to the outside world!__**                                                                                                                                                                                                                                                                                           |
| MASTER              | If true, start the bot in master-mode (default for one-bot-installations). If only one bot is running, then there is only a master.\nIf you have to use more than one bot installation, for multiple DCS servers that are spanned over several locations, you have to install one agent (MASTER = false) at every other location. All DCS servers of that location will then automatically register with that agent. |
| MASTER_ONLY         | True, if this is a master-only installation, set to false otherwise.                                                                                                                                                                                                                                                                                                                                                 |
| SLOW_SYSTEM         | If true, some timeouts are increased to allow slower systems to catch up. Default is false.                                                                                                                                                                                                                                                                                                                          |
| PLUGINS             | List of plugins to be loaded (you usually don't want to touch this).                                                                                                                                                                                                                                                                                                                                                 |
| OPT_PLUGINS         | List of optional plugins to be loaded. Here you can add your plugins that you want to use and that are not loaded by default.                                                                                                                                                                                                                                                                                        |
| AUTOUPDATE          | If true, the bot autoupdates itself with the latest release on startup.                                                                                                                                                                                                                                                                                                                                              |
| AUTOSCAN            | Scan for missions in Saved Games\..\Missions and auto-add them to the mission list (default = false).                                                                                                                                                                                                                                                                                                                |
| GREETING_DM         | A greeting message, that people will receive as a DM in Discord, if they join your guild.                                                                                                                                                                                                                                                                                                                            |
| LOGLEVEL            | The level of logging that is written into the logfile (DEBUG, INFO, WARNING, ERROR, CRITICAL).                                                                                                                                                                                                                                                                                                                       |
| LOGROTATE_COUNT     | Number of logfiles to keep (default: 5).                                                                                                                                                                                                                                                                                                                                                                             |
| LOGROTATE_SIZE      | Number of bytes until which a logfile is rotated (default: 10 MB).                                                                                                                                                                                                                                                                                                                                                   |
| MESSAGE_TIMEOUT     | General timeout for popup messages (default 10 seconds).                                                                                                                                                                                                                                                                                                                                                             | 
| MESSAGE_AUTODELETE  | Delete messages after a specific amount of seconds. This is true for all statistics embeds, LSO analysis, greenieboard, but no usual user commands.                                                                                                                                                                                                                                                                  |
| AUDIT_CHANNEL       | (Optional) The ID of an audit channel where audit events will be logged into. For security reasons, it is recommended that no users can delete messages in this channel.                                                                                                                                                                                                                                             |

b) __ROLES Section__

| Parameter      | Description                                                                                                                   |
|----------------|-------------------------------------------------------------------------------------------------------------------------------|
| Admin          | The name of the admin role in you Discord.                                                                                    |
| DCS Admin      | The name of the role you'd like to give admin rights on your DCS servers (_Moderator_ for instance).                          |
| DCS            | The role of users being able to see their statistics and mission information (usually the general user role in your Discord). |
| GameMaster     | Members of this role can run commands that affect the mission behaviour or handle coalition specific details.                 |

c) __FILTER Section__ (Optional)

| Parameter      | Description                                                                                                                                                                                                                       |
|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| SERVER_FILTER  | Filter to shorten server names (if needed)                                                                                                                                                                                        |
| MISSION_FILTER | Filter to shorten mission names (if needed)                                                                                                                                                                                       |

d) __DCS Section__

| Parameter               | Description                                                                                                                                   |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| DCS_INSTALLATION        | The installation directory of DCS World.                                                                                                      |
| AUTOUPDATE              | If true, your DCS server will be kept up-to-date automatically by the bot (default=false).                                                    |
| SERVER_USER             | The username to display as user no. 1 in the server (aka "Observer")                                                                          |
| MAX_HUNG_MINUTES        | The maximum amount in minutes the server is allowed to not respond to the bot until considered dead (default = 3). Set it to 0 to disable it. |
| MESSAGE_PLAYER_USERNAME | Message that a user gets when being rejected because of a default player name (Player, Spieler, etc.).                                        |

e) __Server Specific Sections__

This section has to be named **exactly** like your Saved Games\<instance> directory. Usual names are DCS.OpenBeta or DCS.openbeta_server.
If your directory is named DCS instead (stable version), just add these fields to the DCS category above.

| Parameter                  | Description                                                                                                                                                                                |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| DCS_HOST                   | The internal (!) IP of the machine, DCS is running onto. If the DCS server is running on the same machine as the bot (default), this should be 127.0.0.1.                                  |
| DCS_PORT                   | Must be a unique value > 1024 of an unused port in your system. This is **NOT** the DCS tcp/udp port (10308), that is used by DCS but a unique different one. Keep the default, if unsure. |
| DCS_HOME                   | The main configuration directory of your DCS server installation (for Hook installation). Keep it empty, if you like to place the Hook by yourself.                                        |
| CHAT_CHANNEL               | The ID of the in-game chat channel to be used for the specific DCS server. Must be unique for every DCS server instance configured. If "-1", no chat messages will be generated.           |
| STATUS_CHANNEL             | The ID of the status-display channel to be used for the specific DCS server. Must be unique for every DCS server instance configured.                                                      |
| ADMIN_CHANNEL              | The ID of the admin-commands channel to be used for the specific DCS server. Must be unique for every DCS server instance configured.                                                      |

### DCS/Hook Configuration
The DCS World integration is done via Hooks. They are being installed automatically into your configured DCS servers by the bot.

### Desanitization
DCSServerBot desanitizes your MissionScripting environment. That means, it changes entries in {DCS_INSTALLATION}\Scripts\MissionScripting.lua.
If you use any other method of desanitization, DCSServerBot checks, if additional desanitizations are needed and conducts them.
**To be able to do so, you must change the permissions on the DCS-installation directory. Give the User group write permissions for instance.**
Your MissionScripting.lua will look like this afterwards:
```lua
do
	sanitizeModule('os')
	--sanitizeModule('io')
	--sanitizeModule('lfs')
	--_G['require'] = nil
	_G['loadlib'] = nil
	--_G['package'] = nil
end
```

### Custom MissionScripting.lua
If you want to use a **custom MissionScripting.lua** that has more sanitization (for instance for LotAtc, Moose, 
OverlordBot or the like) or additional lines to be loaded (for instance for LotAtc, or DCS-gRPC), just place the 
MissionScripting.lua of your choice in the config directory of the bot. It will be replaced on every bot startup then.

### Discord Configuration
The bot uses the following **internal** roles to apply specific permissions to commands.
You can change the role names to the ones being used in your discord. That has to be done in the dcsserverbot.ini 
configuration file. If you want to add multiple groups, separate them by comma (does **not** apply to coalition roles!).

| Role           | Description                                                                                                                                         |
|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| DCS            | People with this role are allowed to chat, check their statistics and gather information about running missions and players.                        |
| DCS Admin      | People with this role are allowed to restart missions, managing the mission list, ban and unban people.                                             |
| Admin          | People with this role are allowed to manage the server, start it up, shut it down, update it, change the password and gather the server statistics. |
| GameMaster     | People with this role can run specific commands that are helpful in missions.                                                                       |

### Sample Configuration
To view some sample configurations for the bot or for each configurable plugin, look [here](./config/README.md).

### Additional Security Features
Players that have no pilot ID (empty) or that share an account with others, will not be able to join your DCS server. 
This is not configurable, it's a general rule (and a good one in my eyes).

---
## Running of the Bot
To start the bot, you can either use the packaged ```run.cmd``` command or ```python run.py```.
<br/>If using _AUTOUPDATE = true_ it is recommended to start the bot via _run.cmd_, as this runs it in a loop as it will 
close itself after an update has taken place.</br>
If you want to run the bot from autostart, create a small batch script, that will change to the bots installation 
directory and run the bot from there like so:
```cmd
@echo off
cd "<whereveryouinstalledthebot>\DCSServerBot"
:loop
python run.py
goto loop
```
If you want to run the bot in a **virtual environment** (because you have other Python programs with different external 
library versions) you can use the ```run-venv.cmd``` batch file to launch the bot.

---
## How to do the more complex stuff?
DCSServerBot can be used to run a whole worldwide distributed set of DCS servers and therefore supports the largest 
communities. The installation and maintenance of such a use-case is just a bit more complex than a single server 
installation.

### Setup Multiple DCS-Servers on a Single Host
DCSServerBot is able to contact DCS-servers at the same machine or over the local network.

To run multiple DCS-servers under control of DCSServerBot(Light) you just have to make sure that you configure different 
communication ports. This can be done with the parameter DCS_PORT in DCSServerBotConfig.lua. The default is 6666, you 
can just increase that for every server (6667, 6668, ...). Don't forget to configure different Discord channels 
(CHAT_CHANNEL, STATUS_CHANNEL and ADMIN_CHANNEL) for every server, too. To add subsequent servers, just follow the steps 
above, and you're good, unless they are on a different Windows server (see below).

DCSServerBot(Light) will autodetect all configured DCS servers on the first startup and generate a sample ini file for 
you already.

### Setup Multiple DCS-Servers at the Same Location
To communicate with DCSServerBot(Light) over the network, you need to change two configurations.
By default, DCSServerBot is configured to be bound to the loopback interface (127.0.0.1) not allowing any external 
connection to the system. This can be changed in dcsserverbot.ini by using the LAN IP address of the Windows server 
running DCSServerBot(Light) instead (NOT your external IP address!).<br/>

**Attention:** The scheduler, .startup and .shutdown commands will only work, if the DCS-servers are on the same machine 
as the bot. So you need to install a bot instance on every server that you use in your network. 
Just configure them as agents (_MASTER = false_) and you are good.

### Setup Multiple Servers on Multiple Host at Different Locations
Works the same as with setting up multiple hosts at the same location. Just configure one bot as MASTER=true and all
others as MASTER=false and you are good. DCSServerBotLight will never be able to do MASTER/AGENT handovers, due to the 
lack of a central database, so you need to make sure that at least one bot is always a master.

### How to talk to the Bot from inside Missions
If you plan to create Bot-events from inside a DCS mission, that is possible! Just make sure, you include this line in a trigger:
```lua
  dofile(lfs.writedir() .. 'Scripts/net/DCSServerBot/DCSServerBot.lua')
```
_Don't use a Mission Start trigger, as this might clash with other plugins loading stuff into the mission._<br/> 
After that, you can for instance send chat messages to the bot using
```lua
  dcsbot.sendBotMessage('Hello World', '12345678') -- 12345678 is the ID of the channel, the message should appear, default is the configured chat channel
```
inside a trigger or anywhere else where scripting is allowed.

**Attention:** Channel always has to be a string, encapsulated with '', **not** a number.

Embeds can be sent using code similar to this snippet:
```lua
  title = 'Special K successfully landed at Kutaisi!'
  description = 'The unbelievable and unimaginable event happend. Special K succeeded at his 110th try to successfully land at Kutaisi, belly down.'
  img = 'https://i.chzbgr.com/full/8459987200/hB315ED4E/damn-instruction-manual'
  fields = {
    ['Pilot'] = 'sexy as hell',
    ['Speed'] = '130 kn',
    ['Wind'] = 'calm'
  }
  footer = 'Just kidding, they forgot to put their gear down!'
  dcsbot.sendEmbed(title, description, img, fields, footer)
```
They will be posted in the chat channel by default, if not specified otherwise (adding the channel id as a last parameter of the sendEmbed() call, see sendBotMessage() above).

If you like to use a single embed, maybe in the status channel, and update it instead, you can do that, too:
```lua
  title = 'RED Coalition captured Kutaisi!'
  description = 'After a successful last bombing run, RED succeeded in capturing the strategic base of Kutaisi.\nBLUE has to fight back **NOW** there is just one base left!'
  dcsbot.updateEmbed('myEmbed', title, description)
  --[....]
  title = 'Mission Over!'
  description = 'RED has won after capturing the last BLUE base Batumi, congratulations!'
  img = 'http://3.bp.blogspot.com/-2u16gMPPgMQ/T1wfXR-bn9I/AAAAAAAAFrQ/yBKrNa9Q88U/s1600/chuck-norris-in-war-middle-east-funny-pinoy-jokes-2012.jpg'
  dcsbot.updateEmbed('myEmbed', title, description, img)
```
If no embed named "myEmbed" is there already, the updateEmbed() call will generate it for you, otherwise it will be replaced with this one.

---
## Contact / Support
If you need support, if you want to chat with me or other users or if you like to contribute, jump into my [Support Discord](https://discord.gg/zjRateN).

If you like what I do and you want to support me, you can do that via my [Patreon Page](https://www.patreon.com/DCS_SpecialK).

---
## Credits
Thanks to the developers of the awesome solutions [HypeMan](https://github.com/robscallsign/HypeMan) and [perun](https://github.com/szporwolik/perun), that gave me the main ideas to this solution.
I gave my best to mark parts in the code to show where I copied some ideas or even code from you guys, which honestly is just a very small piece. Hope that is ok.
