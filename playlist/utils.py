# -*- coding: utf-8 -*-
import hashlib
from subprocess import Popen
import os
import re

from django.conf import settings

#todo move to settings
HOME_DIR = '/srv/pydj'
GBSFM_DIR = '/home/gbsfm'
#GBSFM_DIR = '/home/joop/sites/gbsfm/gbsfm_web'

listeners =  re.compile(r'\<listeners\>(\d+)\</')
#listeners =  re.compile(r'\<CURRENTLISTENERS\>(\d+)\</')

def hashSong(file):
  """Returns sha5 hash of uploaded file. Assumes file is safely closed outside"""
  sha_hash = hashlib.new("")
  if file.multiple_chunks():
    for chunk in file.chunks():
      sha_hash.update(chunk)
  else:
    sha_hash.update(file.read())
  return sha_hash.hexdigest()


def getSong(song):
  return song.getPath()

def restart_stream():
  authstring = "Authorization: Bearer " + settings.DRONE_CI
  print(authstring)
  Popen(["curl", "-ik", "-X", "POST", "https://drone.hemma.lokal/api/repos/scuttle/gbsfm_streamrestart/builds", "-H", authstring], \
  stdin=None, stdout=None, stderr=None, close_fds=True)

def start_stream():
  Popen(["killall", "-KILL", "ices"]).wait()
  olddir = os.curdir
  os.chdir(settings.LOGIC_DIR)
  #f = open(settings.LOGIC_DIR+"/pid", 'w')
  Popen(["ices", "-c", settings.ICES_CONF]).wait()
  #f.close()
  os.chdir(olddir)

def stop_stream():
  Popen(["killall", "-KILL", "ices"]).wait()

def stop_ftp():
  Popen([HOME_DIR + "/doc/killftp.sh"]).wait()

def start_ftp():
  Popen([HOME_DIR + "/doc/killftp.sh"]).wait()
  olddir = os.curdir
  os.chdir(HOME_DIR + '/')
  Popen(["python", "manage.py", "ftp"]).wait()
  os.chdir(olddir)

def restart_ftp():
  authstring = "Authorization: Bearer " + settings.DRONE_CI
  print(authstring)
  Popen(["curl", "-ik", "-X", "POST", "https://drone.hemma.lokal/api/repos/scuttle/gbsfm_ftprestart/builds", "-H", authstring], \
  stdin=None, stdout=None, stderr=None, close_fds=True)

def start_stream2():
  Popen(["killall", "-KILL", "ices"]).wait()
  Popen(["killall", "-KILL", "sc_trans"]).wait()
  olddir = os.curdir
  os.chdir(settings.SCTRANS_DIR)
  Popen(["./sc_trans", "daemon", settings.SCTRANS_CONF]).wait()
  os.chdir(settings.LOGIC_DIR)
  #f = open(settings.LOGIC_DIR+"/pid", 'w')
  Popen(["ices", "-c", settings.ICES_CONF]).wait()
  #f.close()
  os.chdir(olddir)

def stop_stream2():
  Popen(["killall", "-KILL", "ices"]).wait()
  Popen(["killall", "-KILL", "sc_trans"]).wait()

def start_metadataupdater():
  Popen(["killall", "-r", "metadataupdater.sh"], \
  stdin=None, stdout=None, stderr=None, close_fds=True)
  Popen(["nohup", GBSFM_DIR + "/metadataupdater.sh", ">/dev/null", "2>&1&"], \
  stdin=None, stdout=None, stderr=None, close_fds=True)

def stop_metadataupdater():
  Popen(["killall", "-r", "metadataupdater.sh"], \
  stdin=None, stdout=None, stderr=None, close_fds=True)

def start_listeners():
  Popen(["killall", "-r", "listeners.sh"], \
  stdin=None, stdout=None, stderr=None, close_fds=True)
  Popen(["nohup", GBSFM_DIR + "/listeners.sh", ">/dev/null", "2>&1&"], \
  stdin=None, stdout=None, stderr=None, close_fds=True)

def start_remaining():
  Popen(["killall", "-r", "remaining.py"], \
  stdin=None, stdout=None, stderr=None, close_fds=True)
  Popen(["nohup", GBSFM_DIR + "/remaining.py", ">/dev/null", "2>&1&"], \
  stdin=None, stdout=None, stderr=None, close_fds=True)

def start_stream3():
  Popen(["killall", "-KILL", "ices"]).wait()
  Popen(["killall", "-KILL", "sc_trans"]).wait()
  Popen(["killall", "-KILL", "sc_serv"]).wait()
  olddir = os.curdir
  os.chdir(settings.SCSERV_DIR)
  Popen(["./sc_serv", "daemon", settings.SCSERV_CONF]).wait()
  os.chdir(settings.SCTRANS_DIR)
  Popen(["./sc_trans", "daemon", settings.SCTRANS_CONF]).wait()
  os.chdir(settings.LOGIC_DIR)
  #f = open(settings.LOGIC_DIR+"/pid", 'w')
  Popen(["ices", "-c", settings.ICES_CONF]).wait()
  #f.close()
  os.chdir(olddir)

def stop_stream3():
  Popen(["killall", "-KILL", "ices"]).wait()
  Popen(["killall", "-KILL", "sc_trans"]).wait()
  Popen(["killall", "-KILL", "sc_serv"]).wait()

def restart_linkbot():
  Popen([GBSFM_DIR + "/restartstuff.sh", "gbsfm_gbsfm_linkbot", "hub.hemma.lokal/images/gbsfm_linkbot:latest"])

def restart_socks():
  Popen([GBSFM_DIR + "/restartstuff.sh", "gbsfm_socks-docker", "hub.hemma.lokal/images/gbsfm-ircbot:latest"])

def restart_shoes():
  Popen([GBSFM_DIR + "/restartstuff.sh", "gbsfm_shoes-docker", "hub.hemma.lokal/images/gbsfm_discordbot:latest"])

def getObj(table, name, oldid=None):
  #get album/artist object if it exists; otherwise create it
  try:
    entry = table.objects.get(name__exact=name)
    entry.name = name
    entry.save()
    return entry
  except table.DoesNotExist:
    t = table(name=name)
    t.save()
    return t


#def listenerCount(url):
#  try:
#    socket.setdefaulttimeout(5)
#    opener = urllib2.build_opener()
#    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
#    s = opener.open(url).read()
#  except urllib2.URLError:
#    return "??"
#  try:
#    return listeners.search(s).group(1)
#  except (IndexError, AttributeError):
#    return "?"

def listenerCount(url):
  with open(GBSFM_DIR + '/listeners.txt', 'r') as listenerfile:
    listeners = listenerfile.read()
  listenerfile.close()
  return listeners

def gbsfmListenerCount():
  return listenerCount(settings.STREAMINFO_URL)


def try_read(file):
    content = False
    try:
        f = open(file, 'r', encoding='utf-8')
        content = f.read()
    except UnicodeDecodeError:
        pass

    # try again with different encoding
    if not content:
        f = open(file, 'r', encoding='iso-8859-1')
        content = f.read()

    f.close()
    return content.encode('utf-8')
