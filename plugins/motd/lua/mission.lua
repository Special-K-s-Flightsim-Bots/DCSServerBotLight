local base		= _G
dcsbot 			= base.dcsbot

dcsbot.eventHandler = {}
function dcsbot.eventHandler:onEvent(event)
	status, err = pcall(onEvent, event)
	if not status then
		env.warning("DCSServerBot - Error during MOTD:onEvent(): " .. err)
	end
end

function onEvent(event)
    if event then
        local msg = {}
        msg.command = 'onMissionEvent'
        msg.id = event.id
        if event.id ~= world.event.S_EVENT_BIRTH then
            return
        end
        msg.eventName = 'S_EVENT_BIRTH'
        msg.time = event.time
        if event.initiator then
            msg.initiator = {}
            category = event.initiator:getCategory()
            if category == Object.Category.UNIT then
                msg.initiator.type = 'UNIT'
                msg.initiator.unit = event.initiator
                msg.initiator.unit_name = msg.initiator.unit:getName()
                msg.initiator.group = msg.initiator.unit:getGroup()
                if msg.initiator.group and msg.initiator.group:isExist() then
                    msg.initiator.group_name = msg.initiator.group:getName()
                end
                msg.initiator.name = msg.initiator.unit:getPlayerName()
                msg.initiator.coalition = msg.initiator.unit:getCoalition()
                msg.initiator.unit_type = msg.initiator.unit:getTypeName()
                msg.initiator.category = msg.initiator.unit:getDesc().category
            end
            if event.place and event.place:isExist() and event.id ~= world.event.S_EVENT_LANDING_AFTER_EJECTION then
                msg.place = {}
                msg.place.id = event.place.id_
                msg.place.name = event.place:getName()
            end
            dcsbot.sendBotTable(msg)
        end
    end
end

world.addEventHandler(dcsbot.eventHandler)
