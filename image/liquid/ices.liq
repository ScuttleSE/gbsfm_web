set("harbor.bind_addr","0.0.0.0")
set("server.telnet.bind_addr", "0.0.0.0")
set("server.telnet",true)
set("log.file",false)
set("log.stdout",true)
set("log.level",3)
set("init.allow_root",true)

def get_request() =
  result = get_process_lines("python3 /home/liq/getsong.py")
  log("next song: #{result}")
  request.create(list.hd(default="", result))
end

def auth_gbsfm(user, password) =
  ret = get_process_lines("python3 /home/liq/streampw.py #{password}")
  ret = list.hd(default="",ret)
  if ret == "true" then
    true
  else
    false
  end
end

#Website playlist source
gbsfm = request.dynamic(id="gbsfm", get_request)

#Fallback
beees = single("/home/liq/bees.mp3")

#Make sure mono files are being played
gbsfm = audio_to_stereo(gbsfm)

#Put them all together
gbsfm = fallback(track_sensitive=false, [gbsfm, beees])


output.icecast(
    %mp3(bitrate=192),
    fallible = true,
    host = "localhost",
    port = 8000,
    password = "somepassword",
    mount = "192", gbsfm)

output.icecast(
    %mp3(bitrate=256),
    fallible = true,
    host = "localhost",
    port = 8000,
    password = "somepassword",
    mount = "256", gbsfm)

