# -*- coding: utf-8 -*-
import sha
import socket
from subprocess import Popen
import os
import signal
import urllib2
import re

from django.conf import settings

listeners =  re.compile(r'\<listeners\>(\d+)\</')
#listeners =  re.compile(r'\<CURRENTLISTENERS\>(\d+)\</')

def hashSong(file):
  """Returns sha5 hash of uploaded file. Assumes file is safely closed outside"""
  sha_hash = sha.new("")
  if file.multiple_chunks():
    for chunk in file.chunks():
      sha_hash.update(chunk)
  else:
    sha_hash.update(file.read())
  return sha_hash.hexdigest()


def getSong(song):
  return song.getPath()

def restart_stream():
  Popen(["curl", "-k", "-X", "POST", "-F", "token=ea11a2a357d69e0bec99b99e22969c", "-F", "ref=master", "https://gitlab.hemma.lokal/api/v4/projects/48/trigger/pipeline"], \
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
  Popen(["/srv/pydj/doc/killftp.sh"]).wait()

def start_ftp():
  Popen(["/srv/pydj/doc/killftp.sh"]).wait()
  olddir = os.curdir
  os.chdir('/srv/pydj/')
  Popen(["python", "manage.py", "ftp"]).wait()
  os.chdir(olddir)

def restart_ftp():
  Popen(["curl", "-k", "-X", "POST", "-F", "token=5525978610db3c2b32302af0105e11", "-F", "ref=master", "https://gitlab.hemma.lokal/api/v4/projects/49/trigger/pipeline"], \
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
  Popen(["nohup", "/home/gbsfm/metadataupdater.sh", ">/dev/null", "2>&1&"], \
  stdin=None, stdout=None, stderr=None, close_fds=True)

def start_listeners():
  Popen(["killall", "-r", "listeners.sh"], \
  stdin=None, stdout=None, stderr=None, close_fds=True)
  Popen(["nohup", "/home/gbsfm/listeners.sh", ">/dev/null", "2>&1&"], \
  stdin=None, stdout=None, stderr=None, close_fds=True)

def start_remaining():
  Popen(["killall", "-r", "remaining.py"], \
  stdin=None, stdout=None, stderr=None, close_fds=True)
  Popen(["nohup", "/home/gbsfm/remaining.py", ">/dev/null", "2>&1&"], \
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
  Popen(["/home/gbsfm/restartstuff.sh", "botstack_socks-linkbot", "gitlab.hemma.lokal:5005/scuttle/socks-linkbot:latest"])

def restart_socks():
  Popen(["/home/gbsfm/restartstuff.sh", "botstack_socks-docker", "gitlab.hemma.lokal:5005/scuttle/socks-docker:latest"])

def restart_shoes():
  Popen(["/home/gbsfm/restartstuff.sh", "botstack_shoes-docker", "gitlab.hemma.lokal:5005/scuttle/shoes-docker:latest"])

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
  with open('/home/gbsfm/listeners.txt', 'r') as listenerfile:
    listeners = listenerfile.read()
  listenerfile.close()
  return listeners

def gbsfmListenerCount():
  return listenerCount(settings.STREAMINFO_URL)
