local base		= _G
dcsbot 			= base.dcsbot

function dcsbot.getFlag(flag, channel)
    env.info('DCSServerBotLight - Getting flag ' .. flag)
    msg = {}
    msg.command = 'getFlag'
    msg.value = trigger.misc.getUserFlag(flag)
	dcsbot.sendBotTable(msg, channel)
end

function dcsbot.getVariable(name, channel)
    env.info('DCSServerBotLight - Getting variable ' .. name)
    msg = {}
    msg.command = 'getVariable'
    msg.value = _G[name]
	dcsbot.sendBotTable(msg, channel)
end

function dcsbot.setVariable(name, value)
    env.info('DCSServerBotLight - Setting variable ' .. name .. ' to value ' .. value)
    _G[name] = value
end

env.info("DCSServerBotLight - GameMaster: mission.lua loaded.")
