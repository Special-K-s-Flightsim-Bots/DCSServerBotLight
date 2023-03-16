local base  = _G
local dcsbot= base.dcsbot
local utils	= base.require("DCSServerBotUtils")

dcsbot.banList = {}

function dcsbot.kick(json)
    log.write('DCSServerBot', log.DEBUG, 'Admin: kick()')
    if json.id then
        net.kick(json.id, json.reason)
        return
    end
    plist = net.get_player_list()
    for i = 2, table.getn(plist) do
        if ((json.ucid and net.get_player_info(plist[i], 'ucid') == json.ucid) or
                (json.name and net.get_player_info(plist[i], 'name') == json.name)) then
            net.kick(plist[i], json.reason)
            break
        end
    end
end

function dcsbot.ban(json)
    log.write('DCSServerBot', log.DEBUG, 'Admin: ban()')
    if json.id then
        net.banlist_add(json.id, json.period, json.reason)
        return
    end
    plist = net.get_player_list()
    for i = 2, table.getn(plist) do
        if ((json.ucid and net.get_player_info(plist[i], 'ucid') == json.ucid) or
                (json.name and net.get_player_info(plist[i], 'name') == json.name)) then
            net.banlist_add(plist[i], json.period, json.reason)
            break
        end
    end
end

function dcsbot.bans(json)
	local msg = {}
	msg.command = 'bans'
    msg.bans = net.banlist_get()
	utils.sendBotTable(msg, json.channel)
end

function dcsbot.unban(json)
    log.write('DCSServerBot', log.DEBUG, 'Admin: unban()')
	net.banlist_remove(json.ucid)
end

function dcsbot.force_player_slot(json)
    log.write('DCSServerBot', log.DEBUG, 'Admin: force_player_slot()')
    net.force_player_slot(json.playerID, json.sideID or 0, json.slotID or '')
    if json.slotID == 0 and json.reason ~= 'n/a' then
        net.send_chat_to("You have been moved to spectators because of " .. reason, json.playerID)
    else
        net.send_chat_to("You have been moved to spectators by an admin", json.playerID)
    end
end
