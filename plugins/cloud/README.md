# Plugin "Cloud"
We've put together a group consisting of the admins of the most popular DCS servers and we monitor what's going on in 
the community. When we see someone that is crashing servers by hacking or any other **really** (really) bad stuff, we 
put them in the global ban list. Nobody that gets usually banned on a server for misbehaviour will get onto the list. 
There are only the real bad guys on it.</br>
If you opt in to this plugin, you already participate from that ban list. You can chose whether to ban DCS players 
and/or Discord users. Both are active per default.</br>
If you are a server admin of a large server and not part of DGSA, the "DCS Global Server Admins" yet, send me a DM.

## Configuration
```json
{
  "configs": [
    {
      "protocol": "https",
      "host": "dcsserverbot-prod.herokuapp.com",
      "port": 443,    
      "register": true,                                -- Register online to allow general statistics of installations
      "dcs-ban": false,                                -- Auto-ban globally banned DCS players (default).
      "discord-ban": false                             -- Auto-ban globally banned Discord members (default).
    }
  ]
}
```

The online registration helps me to better understand which installations are out there. There is no personal
information sent to the cloud and you can always see what is being sent (dcsserverbot.log) and disable it, if you feel
uncomfortable with it. I would appreciate, if you send me that little bit of data, as it helps me (and you) in
maintaining the solutions that are out in the wild.
