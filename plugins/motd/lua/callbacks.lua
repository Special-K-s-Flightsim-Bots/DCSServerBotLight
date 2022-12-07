local motd  = motd or {}

function motd.onMissionLoadEnd()
    log.write('DCSServerBot', log.DEBUG, 'MOTD: onMissionLoadEnd()')
    net.dostring_in('mission', 'a_do_script("dofile(\\"' .. lfs.writedir():gsub('\\', '/') .. 'Scripts/net/DCSServerBot/DCSServerBot.lua' .. '\\")")')
    net.dostring_in('mission', 'a_do_script("dofile(\\"' .. lfs.writedir():gsub('\\', '/') .. 'Scripts/net/DCSServerBot/motd/mission.lua' .. '\\")")')
end

DCS.setUserCallbacks(motd)
