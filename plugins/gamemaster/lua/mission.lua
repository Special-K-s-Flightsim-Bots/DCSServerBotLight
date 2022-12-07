local base		= _G
dcsbot 			= base.dcsbot

function dcsbot.getFlag(flag, channel)
    log.write('DCSServerBot', log.DEBUG, 'GameMaster: getFlag()')
    msg = {}
    msg.command = 'getFlag'
    msg.value = trigger.misc.getUserFlag(flag)
	dcsbot.sendBotTable(msg, channel)
end

function dcsbot.getVariable(name, channel)
    log.write('DCSServerBot', log.DEBUG, 'GameMaster: getVariable()')
    msg = {}
    msg.command = 'getVariable'
    msg.value = _G[name]
	dcsbot.sendBotTable(msg, channel)
end

function dcsbot.setVariable(name, value)
    log.write('DCSServerBot', log.DEBUG, 'GameMaster: setVariable()')
    _G[name] = value
end
