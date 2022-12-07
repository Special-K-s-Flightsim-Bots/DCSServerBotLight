local base = _G

local dcsbot    = base.dcsbot
local utils 	= base.require("DCSServerBotUtils")

dcsbot.registered = false
dcsbot.banList = {}


function dcsbot.start_server(json)
    net.start_server(utils.loadSettingsRaw())
end

function dcsbot.stop_server(json)
    net.stop_game()
end

function dcsbot.shutdown(json)
    log.write('DCSServerBot', log.DEBUG, 'Admin: shutdown()')
	DCS.exitProcess()
end

function dcsbot.loadParams(json)
    log.write('DCSServerBot', log.DEBUG, 'Admin: loadParams(' .. json.plugin ..')')
    dcsbot.params = dcsbot.params or {}
    dcsbot.params[json.plugin] = json.params
end
