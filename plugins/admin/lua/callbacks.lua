local base   	= _G
local config    = base.require("DCSServerBotConfig")

local default_names = { 'Player', 'Spieler', 'Jugador', 'Joueur' }

local function locate(table, value)
    for i = 1, #table do
        if table[i] == value then return true end
    end
    return false
end

local admin = admin or {}

function admin.onPlayerTryConnect(addr, name, ucid, playerID)
    log.write('DCSServerBot', log.DEBUG, 'Admin: onPlayerTryConnect()')
	local msg = {}
    if locate(default_names, name) then
        return false, config.MESSAGE_PLAYER_USERNAME
    end
end

DCS.setUserCallbacks(admin)
