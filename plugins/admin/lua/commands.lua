local base  = _G
local dcsbot= base.dcsbot

dcsbot.banList = {}

function dcsbot.kick(json)
    log.write('DCSServerBot', log.DEBUG, 'Admin: kick()')
    if json.id then
        net.kick(json.id, json.reason)
        return
    end
    plist = net.get_player_list()
    for i = 1, table.getn(plist) do
        if ((json.ucid and net.get_player_info(plist[i], 'ucid') == json.ucid) or
                (json.name and net.get_player_info(plist[i], 'name') == json.name)) then
            net.kick(plist[i], json.reason)
            break
        end
    end
end

function dcsbot.ban(json)
    log.write('DCSServerBot', log.DEBUG, 'Admin: ban()')
    plist = net.get_player_list()
    if num_players > 1 then
        for i = 2, table.getn(plist) do
            ucid = net.get_player_info(plist[i], 'ucid')
            if ucid == json.ucid then
                net.banlist_add(i, json.period, json.reason)
                return
            end
        end
    end
end

function dcsbot.unban(json)
    log.write('DCSServerBot', log.DEBUG, 'Admin: unban()')
	net.banlist_remove(json.ucid)
end

function dcsbot.force_player_slot(json)
    log.write('DCSServerBot', log.DEBUG, 'Admin: force_player_slot()')
    net.force_player_slot(json.playerID, json.sideID or 0, json.slotID or '')
end
