# Configuration Samples
In this folder, you'll find some configuration-file samples for the bot and the different available plugins.

## dcsserverbot.ini
This sample can be used as a starting point, when you create your own dcsserverbot.ini file.<br/>
It is a basic configuration for a dedicated server setup with two dedicated servers being configured to be used with
the bot. The first instance is the default instance, the 2nd instance is named "instance2". This is what you provide
with -w to the dcs.exe process or how your Saved Games folder is named. 

## admin.json
Default file to support the .download command. Here you can configure which files / patterns you want to support for
DCS Admin users to download from your server. You see a lot of examples in there already. If you don't want people to
download specific items, just remove the respective line from your admin.json.

## commands.json
This shows two examples of custom commands you can create with the commands plugin. One command starts a DCS server
and the 2nd command runs a `dir` command on your server and returns the output. 

## motd.json
This sample contains a default section, that is being used for every server, if nothing else is provided and a specific
section for server "DCS.openbeta_server", that is overwriting the default.

## scheduler.json
The scheduler is a very powerful and thus complex plugin. I tried to pack in as much information that was possible into
the sample, but you might want to look into the [README](../../plugins/scheduler/README.md) as well.

### Default-Section
Contains the "warn schedule", meaning at which amount of seconds before a restart / shutdown happens, the users should 
get warned. And a list of weather presets, that can be applied to your missions. Both are optional and need only to be
in your configuration, if you want to warn users or if you want to change the weather on demand.

### DCS.openbeta_server
This sample shows the configuration for the first server. It will run 24/7 but only on threads 2 and 3 (aka core 1).

### mission
This is an example for a mission-only server, where missions start on Sunday at 1800 local time. The server will be 
stopped again automatically on Sunday 24:00 / Monday 00:00 if not stopped manually before.

### instance2
This server will run every day 00:00h to 12:00h. It will rotate its missions every 4 hours, even if the server
is populated (people flying on it). From 00:00 to 08:00 the "Winter Nighttime" preset will be used, between
08:00 and 12:00, the "Winter Daytime" preset.
Two external lua files will be loaded on mission start and on mission end. When the server shuts down, the whole PC 
will reboot with the onShutdown parameter (bot needs to run with Admin rights for such a case).

### instance3
This server runs every day from 12:00 until 24:00. The mission and DCS server restarts after 8hrs mission time 
(480 mins), but only if nobody is flying on the server (populated = false). Whenever the mission restarts, a random
preset will be picked out of the provided list ("Winter Daytime", "Summer Daytime").
