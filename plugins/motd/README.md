# Plugin MessageOfTheDay (MOTD)
This plugin adds a message of the day to the server, that is displayed either on join or when you hop into a plane.

## Configuration
The plugin is configured via JSON, as many others. If you don't generate your custom json file (sample available in the 
config directory), the plugin will not generate any messages.

```json
{
  "configs": [
    {
      "on_birth": {                                                             -- whenever a user joins a plane
        "message": "{player[name]}, welcome to {server[server_name]}!",         -- OR
        "report": "greetings.json",                                             -- report file, has to be placed in /reports/motd
        "display_type": "popup",                                                -- chat or popup
        "display_time": 20                                                      -- only relevant for popup
      },
      "nudge": {
        "delay": 600,                                                           -- every 10 mins
        "message": "This awesome server is presented to you by https://discord.gg/myfancylink.\nCome and join us!",
        "display_type": "popup",
        "display_time": 20
      }
    },
    {
      "installation": "DCS.openbeta_server",
      "on_join": {                                                              -- whenever a user joins the server
        "message": "Welcome to our public server! Teamkills will be punished."
      }
    }
  ]
}
```
