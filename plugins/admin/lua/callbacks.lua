local base   	= _G
local config    = base.require("DCSServerBotConfig")

local default_names = {
    'Player',
    'Joueur',
    'Spieler',
    'Игрок',
    'Jugador',
    '玩家',
    'Hráč',
    '플레이어'
}

local function locate(table, value)
    for i = 1, #table do
        if table[i]:lower() == value:lower() then return true end
    end
    return false
end

local admin = admin or {}

admin.last_change_slot = {}
admin.num_change_slots = {}


function admin.onPlayerTryConnect(addr, name, ucid, playerID)
    log.write('DCSServerBot', log.DEBUG, 'Admin: onPlayerTryConnect()')
	local msg = {}
    if locate(default_names, name) then
        return false, config.MESSAGE_PLAYER_DEFAULT_USERNAME
    end
    name2 = name:gsub("[\r\n%z]", "")
    if name ~= name2 then
        return false, config.MESSAGE_PLAYER_USERNAME
    end
    if name:find(']', 1, true) or name:find('[', 1, true) or name:find('\\', 1, true) then
        return false, 'Please change your username to latin characters only, as there is a temporary issue with dynamic spawns'
    end
end

function admin.onPlayerConnect(playerID)
    log.write('DCSServerBot', log.DEBUG, 'Admin: onPlayerConnect()')
	admin.last_change_slot[playerID] = nil
	admin.num_change_slots[playerID] = 0
end

function admin.onPlayerTryChangeSlot(playerID, side, slotID)
    log.write('DCSServerBot', log.DEBUG, 'Admin: onPlayerTryChangeSlot()')
    -- ignore slot requests that have been done when the player was kicked already
    if admin.num_change_slots[playerID] == -1 then
        return false
    end
	if admin.last_change_slot[playerID] and admin.last_change_slot[playerID] > (os.clock() - 2) then
		admin.num_change_slots[playerID] = admin.num_change_slots[playerID] + 1
		if admin.num_change_slots[playerID] > 5 then
            admin.num_change_slots[playerID] = -1
			net.kick(playerID, config.MESSAGE_SLOT_SPAMMING)
			return false
        end
	else
		admin.last_change_slot[playerID] = os.clock()
    	admin.num_change_slots[playerID] = 0
	end
end

DCS.setUserCallbacks(admin)
