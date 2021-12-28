# -*- coding: utf-8 -*-

    #######################################################################
    # This file is part of the g2 project.                                #
    #                                                                     #
    # g2 is free software: you can redistribute it and/or modify          #
    # it under the terms of the Affero General Public License, Version 1  #
    # (as published by Affero, Incorporated) but not any later            #
    # version.                                                            #
    #                                                                     #
    # g2 is distributed in the hope that it will be useful,               #
    # but WITHOUT ANY WARRANTY; without even the implied warranty of      #
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the        #
    # Affero General Public License for more details.                     #
    #                                                                     #
    # You can find a copy of the Affero General Public License, Version 1 #
    # at http://www.affero.org/oagpl.html.                                #
    #######################################################################
import tempfile
from random import getrandbits
import random
from hashlib import md5
from urllib.error import URLError
from subprocess import Popen
from itertools import chain
import logging
import json
import base64

from django.http import *
from django.template import Context, loader
from django.urls import reverse
from django.core.serializers import serialize
from django.contrib.auth.models import User,  UserManager, Group, Permission
from django.shortcuts import render
import django.contrib.auth.views
import django.contrib.auth as auth
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template import RequestContext
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Avg, Max, Min, Count, Q
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import permission_required, login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages


from playlist.forms import *
from playlist.models import *
from playlist.utils import getSong, getObj, gbsfmListenerCount
from playlist.upload import UploadedFile
from playlist.search import Search
from playlist.cue import CueFile
from playlist.pllib import Playlist

LIVE = settings.IS_LIVE

if LIVE:
    from playlist.sa import SAProfile, IDNotFoundError


PIDFILE = settings.LOGIC_DIR+"/pid"
SA_PREFIX = "http://forums.somethingawful.com/member.php?action=getinfo&username="
MAX_EVENTS = 20 #maximum number of events premissible for one event type


def now():
  return " ".join(datetime.datetime.now().isoformat().split("T"))


@permission_required('playlist.start_stream')
def restart_stream(request):
  utils.restart_stream()
  return HttpResponseRedirect(reverse('g2admin'))

@permission_required('playlist.start_stream')
def start_metadataupdater(request):
  utils.start_metadataupdater()
  return HttpResponseRedirect(reverse('g2admin'))

@permission_required('playlist.start_stream')
def stop_metadataupdater(request):
  utils.stop_metadataupdater()
  return HttpResponseRedirect(reverse('g2admin'))

@permission_required('playlist.start_stream')
def start_listeners(request):
  utils.start_listeners()
  return HttpResponseRedirect(reverse('g2admin'))

@permission_required('playlist.start_stream')
def start_remaining(request):
  utils.start_remaining()
  return HttpResponseRedirect(reverse('g2admin'))

@permission_required('playlist.stop_stream')
def stop_stream(request):
  utils.stop_stream()
  return HttpResponseRedirect(reverse('g2admin'))

@permission_required('playlist.start_stream')
def start_stream2(request):
  utils.start_stream2()
  return HttpResponseRedirect(reverse('g2admin'))

@permission_required('playlist.stop_stream')
def stop_stream2(request):
  utils.stop_stream2()
  return HttpResponseRedirect(reverse('g2admin'))

@permission_required('playlist.start_stream')
def start_stream3(request):
  utils.start_stream3()
  return HttpResponseRedirect(reverse('g2admin'))

@permission_required('playlist.stop_stream')
def stop_stream3(request):
  utils.stop_stream3()
  return HttpResponseRedirect(reverse('g2admin'))

@permission_required('playlist.start_stream')
def start_ftp(request):
  utils.start_ftp()
  return HttpResponseRedirect(reverse('g2admin'))

@permission_required('playlist.start_stream')
def restart_ftp(request):
  utils.restart_ftp()
  return HttpResponseRedirect(reverse('g2admin'))

@permission_required('playlist.stop_stream')
def stop_ftp(request):
  utils.stop_ftp()
  return HttpResponseRedirect(reverse('g2admin'))

@permission_required('playlist.stop_stream')
def restart_socks(request):
  utils.restart_socks()
  return HttpResponseRedirect(reverse('g2admin'))

@permission_required('playlist.stop_stream')
def restart_shoes(request):
  utils.restart_shoes()
  return HttpResponseRedirect(reverse('g2admin'))

@permission_required('playlist.stop_stream')
def restart_linkbot(request):
  utils.restart_linkbot()
  return HttpResponseRedirect(reverse('g2admin'))

@permission_required('playlist.view_g2admin')
def g2admin(request):
  if request.method == "POST":
    msgform = WelcomeMsgForm(request.POST)
    if msgform.is_valid():
      msg = Settings.objects.get(key="welcome_message")
      msg.value = msgform.cleaned_data['message']
      msg.save()
  else:
    msgform = WelcomeMsgForm(initial={'message':Settings.objects.get(key="welcome_message").value})
  return render(request, 'admin.html',  {"msgform":msgform})

#Livestream PW
@permission_required('playlist.view_g2admin')
#def g2admin(request):
def g2streampw(request):
  if request.method == "POST":
    pwform = StreamPwForm(request.POST)
    if pwform.is_valid():
      msg = Settings.objects.get(key="stream_password")
      msg.value = pwform.cleaned_data['message']
      msg.save()
  else:
    pwform = StreamPwForm(initial={'message':Settings.objects.get(key="stream_password").value})
  return render(request, 'admin.html',  {"pwform":pwform})

def splaylist(request):
  #for scuttle loadtesting
  try:
    if authenticate(username=request.GET['username'], password=request.GET['password']):
      return jsplaylist(request)
  except KeyError:
    return HttpResponseRedirect(reverse('login'))

@permission_required('playlist.view_playlist')
def playlist(request, lastid=None):
  #normal entry route
  if "gbsfm.ath.cx" in request.get_host():
    return HttpResponseRedirect("/images/moved.html")
  return jsplaylist(request, lastid)

@permission_required('playlist.view_playlist')
def carplay(request, lastid=None):
  return render(request, 'carplay.html')

def jsplaylist(request, lastid=None):

  if lastid is None:
    try:
      historylength = request.user.userprofile.s_playlistHistory
    except AttributeError:
      historylength = 10

  aug_playlist = Playlist(request.user, historylength).fullList()
  accuracy = 1 #TODO: make accuracy user setting
  can_skip = request.user.has_perm('playlist.skip_song')
  lastremoval = RemovedEntry.objects.aggregate(Max('id'))['id__max']
  try:
    welcome_message = Settings.objects.get(key="welcome_message").value
  except:
    welcome_message = None

  length = PlaylistEntry.objects.length()

  return render(request, 'jsplaylist.html',  {'aug_playlist': aug_playlist, 'can_skip':can_skip,
  'lastremoval':lastremoval, 'welcome_message':welcome_message,
  'length':length, 'accuracy':accuracy})


 # return render(request, 'index.html',  {'aug_playlist': aug_playlist, 'msg':msg, 'can_skip':can_skip})


@login_required()
def ajax(request):
    events = []
    length_changed = False #True if any actions would have changed the playlist length

    #new removals
    last_removal = int(request.GET.get('last_removal', -1))

    if last_removal != -1:
      removals = RemovedEntry.objects.filter(id__gt=last_removal)
      removal_events = []
      if removal_events:
        length_changed = True
      for removal in removals:
        removal_events.append(('removal', {"entryid": removal.oldid, "id": removal.id}))
      if len(removal_events) > MAX_EVENTS:
        removal_events = removal_events[:MAX_EVENTS]
      events.extend(removal_events)




    #get now playing track
    try:
      client_playing = int(request.GET.get('now_playing', 0))
    except ValueError:
      client_playing = 0
    #always output as if this isn't given it's definitely needed
    server_playing = PlaylistEntry.objects.nowPlaying()

    #check for submitted comment
    if request.user.has_perm("playlist.can_comment"):
      try:
        comment = request.GET['comment']
      except KeyError:
        pass
      else:
        server_playing.song.comment(request.user, comment)
        #TODO: handle comment being too long gracefully

    #check for submitted vote
    if request.user.has_perm("playlist.can_rate"):
      try:
        vote = request.GET['vote']
      except KeyError:
        pass
      else:
        server_playing.song.rate(vote, request.user)

    if server_playing.id != client_playing:
      events.append(('now_playing', server_playing.id))
      length_changed = True
      #new title needed
      try:
        events.append(('metadata', PlaylistEntry.objects.nowPlaying().song.metadataString()))
        linkedMetadata = render_to_string('linked_metadata.html', request=request)
        events.append(('linkedMetadata', linkedMetadata))
      except PlaylistEntry.DoesNotExist:
        pass
      #new song length needed
      events.append(('songLength', PlaylistEntry.objects.nowPlaying().song.length))
      #new comments needed
      events.append(('clearComments', ''))
      comments = server_playing.song.comments.all().order_by("time") #ensure oldest first - new comments are placed at top of update list
      for comment in comments:
        events.append(comment.ajaxEvent())
    else:
      try:
        last_comment = int(request.GET['last_comment'])
      except (ValueError, TypeError, KeyError):
        pass
      else:
        comments = server_playing.song.comments.all().order_by("datetime").filter(id__gt=last_comment)
        for comment in comments:
          events.append(comment.ajaxEvent())

    #send user vote & song avg vote_count
    try:
      user_vote = server_playing.song.ratings.get(user=request.user).score
    except Rating.DoesNotExist:
      user_vote = 0

    if server_playing.song.voteno == 1:
      score_str = "%.1f (%d vote)" % (server_playing.song.avgscore, server_playing.song.voteno)
    elif server_playing.song.voteno > 1:
      score_str = "%.1f (%d votes)" % (server_playing.song.avgscore, server_playing.song.voteno, )
    else:
      score_str = "no votes"
    events.append(('userVote', int(user_vote)))
    events.append(('score', score_str))

    #new adds
    try:
      last_add = int(request.GET['last_add'])
    except (ValueError, TypeError, KeyError):
      pass
    else:
      accuracy = 1 #TODO: replace with user setting
      aug_playlist = Playlist(request.user).fromLastID(last_add)
      if len(aug_playlist) > 0:
        length_changed = True
        if len(aug_playlist) > MAX_EVENTS:
          aug_playlist = aug_playlist[:MAX_EVENTS]
        html = render_to_string('playlist_table.html',  {'aug_playlist': aug_playlist, 'accuracy':accuracy},
        request=request)

        events.append(("adds", html))




    if length_changed:
      length = PlaylistEntry.objects.length()
      events.append(('pllength', render_to_string('pl_length.html', {'length':length})))

    #handle cuefile stuff
    tolerance = 5 #tolerance in seconds between real and recieved time TODO: replace with internal setting

    position = request.GET.get('position', None)
    if position:
      #cue = CueFile(settings.LOGIC_DIR + "/work/ices.cue")
      cue = CueFile("/remaining/ices2.cue")
      now_playing = PlaylistEntry.objects.nowPlaying().song
      if abs(int(position) - cue.getTime(now_playing)) >= tolerance:
        events.append(('songPosition', cue.getTime(now_playing)))

    return HttpResponse(json.dumps(events))

@csrf_exempt
def api(request, resource=""):

  #authentication
  if request.user.is_authenticated:
    user = request.user
  else: #non-persistent authentication for things like bots and clients
    try:
      username = request.GET['username']
    except KeyError:
      try: #is there a userid arg?
        username = User.objects.get(id=request.GET['userid']).username
      except (User.DoesNotExist, KeyError):
        return HttpResponseForbidden()
    try: #try using password
      password = request.GET['password']
      user = authenticate(username=username, password=password)
      if user is None:
        return HttpResponseForbidden()
    except KeyError:
      try: #try api_key
        api_key = request.GET['key']
        userprofile = UserProfile.objects.get(user__username=username, api_key=api_key)
        user = userprofile.user
        if not userprofile.api_key: #api key not yet set
          return HttpResponseForbidden()
      except (KeyError, User.DoesNotExist):
        return HttpResponseForbidden()

  if resource == "nop":
    return HttpResponse("1")

  if resource == "restartftp":
    Popen(["/srv/pydj/doc/killftp.sh"]).wait()
    olddir = os.curdir
    os.chdir('/srv/pydj/')
    Popen(["python", "manage.py", "ftp"])
    os.chdir(olddir)
    return HttpResponse("ftp_restarted")

  if resource == "nowplaying":
    try:
      entryid = PlaylistEntry.objects.nowPlaying().id
      return HttpResponse(str(entryid))
    except PlaylistEntry.DoesNotExist:
      return HttpResponse()

  if resource == "merge":
    if not user.has_perm("playlist.merge_song"):
      return HttpResponseForbidden()
    try:
      old = Song.objects.get(id=request.GET['old'])
      new = Song.objects.get(id=request.GET['new'])
    except KeyError:
      return HttpResponseBadRequest #args insufficient
    except Song.DoesNotExist:
      raise Http404 #songs don't exist

    logging.info("Mod %s (uid %d) merged song with sha_hash %s into %d at %s" %
      (request.user.username, request.user.id, old.sha_hash, new.id, now()))

    new.merge(old)
    return HttpResponse()



  if resource == "deletions":
    try:
      lastid = request.GET['lastid']
    except KeyError:
      lastid = 0
    if not lastid: lastid = 0 #in case of "&lastid="
    deletions = RemovedEntry.objects.filter(id__gt=lastid)
    data = serialize("json", deletions, fields=('oldid'))
    return HttpResponse(data)



  if resource == "adds":
    try:
      lastid = request.GET['lastid']
    except KeyError:
      lastid = 0
    if not lastid: lastid = 0
    adds = PlaylistEntry.objects.extra(select={"user_vote": "SELECT ROUND(score, 0) FROM playlist_rating WHERE playlist_rating.user_id = \
    %s AND playlist_rating.song_id = playlist_playlistentry.song_id", "avg_score": "SELECT AVG(playlist_rating.score) FROM playlist_rating WHERE playlist_rating.song_id = playlist_playlistentry.song_id", "vote_count": "SELECT COUNT(*) FROM playlist_rating WHERE playlist_rating.song_id = playlist_playlistentry.song_id"},
    select_params=[request.user.id]).select_related("song__artist", "song__album", "song__uploader", "adder").order_by('addtime').filter(id__gt=lastid)
    data = serialize("json", adds, relations={'song':{'relations':('artist'), 'fields':('title', 'length', 'artist', 'avgscore')}, 'adder':{'fields':('username')}})
    return HttpResponse(data)

  #if resource == "history":
    #try:
      #lastid = request.GET['lastid']
    #except KeyError:
      #raise Http404
    #if not lastid: raise Http404
    #if lastid[0] != 'h':
      #raise Http404 #avert disaster
    #lastid = lastid[1:] #get rid of leading 'h'
    #history = OldPlaylistEntry.objects.select_related().filter(id__gt=lastid)
    #data = serialize("json", history, relations={'song':{'relations':('artist'), 'fields':('title', 'length', 'artist')}, 'adder':{'fields':('username')}})
    #return HttpResponse(data)

  if resource == "pltitle":
    try:
      return HttpResponse(PlaylistEntry.objects.nowPlaying().song.metadataString() + " - GBS-FM")
    except PlaylistEntry.DoesNotExist:
      return HttpResponse("GBS-FM")


  if resource == "pltitle2":
    try:
      return HttpResponse(PlaylistEntry.objects.nowPlaying().song.metadataString())
    except PlaylistEntry.DoesNotExist:
      return HttpResponse("GBS-FM")


  def getSong(request):
    """Returns a song object given a request object"""
    try:
      songid = request.GET['songid']
      songid = int(songid)
      song = Song.objects.get(id=songid)
    except KeyError:
      song = PlaylistEntry.objects.nowPlaying().song
    except ValueError:
      if songid == "curr":
        song = PlaylistEntry.objects.nowPlaying().song
      elif songid == "prev":
        song = OldPlaylistEntry.objects.select_related("song").extra(where=['playlist_oldplaylistentry.id =\
        (select max(playlist_oldplaylistentry.id) from playlist_oldplaylistentry)'])[0].song
    return song

  if resource == "favourite":
    song = getSong(request)
    if song in user.userprofile.favourites.all():
      state = "old favourite"
    else:
      user.userprofile.favourites.add(song)
      state = "new favourite"
    return HttpResponse(song.metadataString() +'\n' + state)

  if resource == "unfavourite":
    song = getSong(request)
    user.userprofile.favourites.remove(song)
    return HttpResponse(song.metadataString())

  #if resource == "getuser":
    #try:
      #user = User.objects.get(username=request.GET['username'])
    #except KeyError:
      #user = request.user
    #except User.DoesNotExist:
      #raise Http404

    #return HttpResponse(user.id)

  if resource == "getfavourite":
    """
    Get a song from favourites of the specified user (ID: userid).
    Trys to make it addable but will return best unaddable one otherwise.
    """
    try:
      lover = User.objects.get(id=int(request.GET['loverid']))
    except KeyError:
      try:
        lover = User.objects.get(username=str(request.GET['lovername']))
      except KeyError:
        lover = user
    songs = lover.userprofile.favourites.all().check_playable(user)
    unplayed = songs.filter(on_playlist=False, banned=False) #TODO: use recently_played too!
    if unplayed: #only use it if there are actually unplayed songs!
      songs = unplayed
    try:
      song = random.SystemRandom().choice(songs)
    except:
      raise Http404

    return HttpResponse(str(song.id) + "\n" + song.metadataString())

  if resource == "vote":
    if not user.has_perm("playlist.can_rate"):
      return HttpResponseForbidden()
    try:
      vote = float(request.GET['vote'])
    except KeyError:
      raise Http404
    song = getSong(request)
    prevscore = song.rate(vote, user)

    return HttpResponse(str(prevscore) + " " +song.metadataString())

  if resource == "comment":
    if not user.has_perm("playlist.can_comment"):
      return HttpResponseForbidden()
    try:
      comment = request.GET['comment']
    except KeyError:
      raise Http404
    song = getSong(request)
    time = song.comment(user, comment)

    return HttpResponse(str(time))

  if resource == "pllength":
    length = PlaylistEntry.objects.length()
    try:
      comment = request.GET['formatted']
      return render(request, 'pl_length.html', {'length':length})
    except KeyError:
      return HttpResponse(str(length['seconds']) + '\n' + str(length['song_count']))

  if resource == "add":
    if not user.has_perm("playlist.queue_song"):
      return HttpResponseForbidden()
    try:
      song = Song.objects.select_related().get(id=request.GET['songid'])
    except (KeyError, Song.DoesNotExist):
      raise Http404

    try:
      song.playlistAdd(user)
    except AddError as e:
      return HttpResponseBadRequest(e.args[0])

    return HttpResponse(song.metadataString())

  if resource == "uncomment":
    try:
      comment = Comment.objects.select_related().filter(user=user)[0]
      comment.delete()
    except IndexError:
      raise Http404

    return HttpResponse(comment.song.metadataString())

  if resource == "metadata":
    song = getSong(request)
    return HttpResponse(song.artist.name + "\n" + song.album.name + "\n" + song.title)

  if resource == "metadata2":
    song = getSong(request)
    return HttpResponse(song.artist.name + "\n" + song.album.name + "\n" + song.title + "\n" + str(song.length))

  if resource == "randid":
    randomid = randomdongid()
    return HttpResponse(int(randomid[0]))

  if resource == "plinfo":
    pldongid = request.GET.get('plid', 0)
    playlistinfo = plinfoq(pldongid)
    return HttpResponse(str(playlistinfo[0]) + "\n" + playlistinfo[2] + "\n" + playlistinfo[3] + "\n" + playlistinfo[1])
    #return HttpResponse(playlistinfo)

  if resource == "listeners":
    return HttpResponse(gbsfmListenerCount())

  if resource == "users":
    return HttpResponse(User.objects.all().count())

  if resource == "position":
    #cue = CueFile(settings.LOGIC_DIR + "/work/ices.cue")
    cue = CueFile("/remaining/ices2.cue")
    d = {}
    now_playing = PlaylistEntry.objects.nowPlaying().song
    d['position'] = cue.getTime(now_playing)
    d['progress'] = cue.getProgress()
    d['length'] = now_playing.length
    return HttpResponse(json.dumps(d))

  if resource == "upload" and request.method == "POST":
    temp_filename = ""
    try:
      filename = request.POST["filename"]
      # base64 encoded
      filecontents = request.POST["filecontents"]

      with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        decoded = base64.urlsafe_b64decode(filecontents)
        f.write(decoded)
        f.flush()
        temp_filename = f.name

      if (temp_filename != ""):
        user.userprofile.uploadSong(UploadedFile(temp_filename, filename))
      else:
        raise Exception("Empty filename.")

    except DuplicateError:
      messages.add_message(request, messages.ERROR, "Error: track already uploaded")
    except FileTooBigError:
      messages.add_message(request, messages.ERROR, "Error: file too big")
    except StorageError:
      messages.add_message(request, messages.ERROR, "Error: file could not be stored!")
      messages.add_message(request, messages.ERROR, "Uploaded file successfully!")
    except Exception as ex:
      messages.add_message(request, messages.ERROR, "Error: Your request has errors in it. File might be unparsable by ffprobe.")
      messages.add_message(request, messages.ERROR, ex)
    else:
      messages.add_message(request, messages.SUCCESS, "Uploaded file successfully!")
      if (temp_filename != ""):
        os.remove(temp_filename)
      return HttpResponse(status=200)
    finally:
      if (temp_filename != ""):
        os.remove(temp_filename)
    return HttpResponseBadRequest("\n".join([str(x) for x in messages.get_messages(request)]))

  raise Http404

@login_required()
def favourite(request, songid=0):
  try:
    song = Song.objects.get(id=songid)
  except Song.DoesNotExist:
    raise Http404
  request.user.userprofile.favourites.add(song)
  messages.add_message(request, messages.SUCCESS, "Song favourited successfully")

  referrer = request.META.get('HTTP_REFERER', None)
  if referrer:
    return HttpResponseRedirect(referrer)
  else:
    return HttpResponseRedirect(reverse('playlist'))

@login_required()
def unfavourite(request, songid=0):
  try:
    song = Song.objects.get(id=songid)
  except Song.DoesNotExist:
    raise Http404
  request.user.userprofile.favourites.remove(song)
  messages.add_message(request, messages.SUCCESS, "Song unfavourited successfully")

  referrer = request.META.get('HTTP_REFERER', None)
  if referrer:
    return HttpResponseRedirect(referrer)
  else:
    return HttpResponseRedirect(reverse('playlist'))


@login_required()
def user_settings(request):
  profile = request.user.userprofile
  if not profile.api_key:
    keygen(request)
  api_key = profile.api_key

  if request.method == "POST":
    password_form = PasswordChangeForm(request.user, request.POST)
    if password_form.is_valid():
      password_form.save() #resets password appropriately
      messages.add_message(request, messages.SUCCESS, "Password changed successfully")

  else:
    password_form = PasswordChangeForm(request.user)

  return render(request, 'user_settings.html', {'api_key': api_key, 'password_form': password_form})

@login_required()
def keygen(request):
  """Generates an API key which can be used instead of a password for API calls but not for important things like deletes. Checks for dupes."""
  while True:
    #keep generating keys until we get a unique one
    to_hash = settings.SECRET_KEY + str(getrandbits(64)) + request.user.username
    newquay = lambda: md5(to_hash.encode('utf-8')).hexdigest()
    key = newquay()
    try:
      UserProfile.objects.get(api_key=key)
    except UserProfile.DoesNotExist:
     break
  profile = request.user.userprofile
  profile.api_key = key
  profile.save()
  return HttpResponseRedirect(reverse('user_settings'))

@login_required()
def removeentry(request, entryid):
  try:
    entry = PlaylistEntry.objects.select_related().get(id=entryid)
  except PlaylistEntry.DoesNotExist:
    raise Http404
  if ((entry.adder == request.user) or request.user.has_perm("playlist.remove_entry")) and not entry.playing:
    logging.info("User %s (uid %d) removed songid %d from playlist at %s" % (request.user.username, request.user.id, entry.song.id, now()))
    entry.remove()
    messages.add_message(request, messages.SUCCESS, "Entry deleted successfully")

  else:
    messages.add_message(request, messages.ERROR, "Error: insufficient permissions to remove entry")

  if request.is_ajax():
    return HttpResponse(status=200)
  else:
    return HttpResponseRedirect(reverse('playlist'))

@permission_required('playlist.skip_song')
def skip(request):
  logging.info("Mod %s (uid %d) skipped song at %s" % (request.user.username, request.user.id, now()))
  #Popen(["killall", "-SIGUSR1", "ices"])
  Popen(["/home/gbsfm/skipsong.sh"])
  return HttpResponseRedirect(reverse('playlist'))

@permission_required('playlist.merge_song')
def merge_song(request, mergeeid, mergerid):
  """
  Merge song merger into mergee, resulting in the destruction of song merger
  """
  try:
    merger = Song.objects.get(id=mergerid)
    mergee = Song.objects.get(id=mergeeid)
  except Song.DoesNotExist:
    raise Http404

  logging.info("Mod %s (uid %d) merged song with sha_hash %s into %d at %s" %
    (request.user.username, request.user.id, merger.sha_hash, mergee.id, now()))

  mergee.merge(merger)
  messages.add_message(request, messages.SUCCESS, "Song merged in successfully")

  return HttpResponseRedirect(reverse('song', args=[mergee.id]))

@permission_required('playlist.view_edits')
def edit_queue(request, approve=None, deny=None):
  if approve:
    edit = SongEdit.objects.select_related().get(id=approve)
    edit.apply(request.user)
    return HttpResponseRedirect(reverse('edit_queue'))
  if deny:
    edit = SongEdit.objects.select_related().get(id=deny)
    edit.deny(request.user)
    return HttpResponseRedirect(reverse('edit_queue'))

  edits = SongEdit.objects.select_related().filter(applied=False, denied=False).order_by('created_at')
  edits_list = []
  for edit in edits:
    edit_dict = {}
    edit_dict['id'] = edit.id
    edit_dict['song'] = edit.song
    edit_dict['user'] = edit.requester
    edit_dict['fields'] = []
    for field_edit in edit.field_edits.all():
      edit_dict['fields'].append({'name': field_edit.field,
                        'old_value': getattr(edit.song, field_edit.field),
                        'new_value': field_edit.new_value
                        })
    edits_list.append(edit_dict)
  return render(request, 'edit_queue.html',
         {'edits': edits_list})

@permission_required('playlist.approve_reports')
def reports(request, approve=None, deny=None):
  if approve:
    report = SongReport.objects.select_related().get(id=approve)
    report.approve(request.user)
    return HttpResponseRedirect(reverse('reports'))
  if deny:
    report = SongReport.objects.select_related().get(id=deny)
    report.deny(request.user)
    return HttpResponseRedirect(reverse('reports'))
  reports = SongReport.objects.select_related().filter(approved=False, denied=False).order_by('created_at')
  return render(request, 'reports.html', {'reports': reports})

@login_required()
def song_report(request, songid):
  """View for song report page, handling displaying report form and saving report form data."""
  try:
    song = Song.objects.select_related().get(id=songid)
  except Song.DoesNotExit:
    raise Http404

  if request.method == "POST":
    report_form = ReportForm(request.POST)
    if report_form.is_valid():
      report = report_form.save(commit=False)
      report.song = song
      report.reporter = request.user
      report.save()
      messages.add_message(request, messages.SUCCESS, "Dong successfully reported.")
      return HttpResponseRedirect(reverse('song', kwargs={'songid': songid}))
    else:
      for field in report_form:
        print(field.errors)
  else:
    report_form = ReportForm()
#  return render('song_report.html', {'form': report_form, 'song': song})
  return render(request, 'song_report.html', {'form': report_form, 'song': song})


@permission_required('playlist.view_song')
def song(request, songid=0, edit=None):
  try:
    song = Song.objects.select_related("uploader", "artist", "album", "location").get(id=songid)
  except Song.DoesNotExist:
    raise Http404



  if request.method == "POST":
    editform = SongForm(request.POST, instance=song)
    if editform.is_valid():

      if (request.user.has_perm('playlist.edit_song') or (request.user == song.uploader)):
        #user has correct permissions to edit song
        editform.save()
        logging.info("User/mod %s (uid %d) edited songid %d at %s" % (request.user.username, request.user.id, song.id, now()))
      else:
        #queue a SongEdit
        old_song = Song.objects.get(id=editform.instance.id) #original version of song
        edited_song = editform.save(commit=False) #edited version of song

        song_edit = SongEdit(requester=request.user, song=old_song)
        song_edit.save()
        #MUST CHANGE IF TAGS CHANGE (sorry code nazis)
        for field in ["title", "composer", "lyricist", "remixer", "genre", "track"]:
          if getattr(edited_song, field) != getattr(old_song, field):
            FieldEdit(field=field, new_value=getattr(edited_song, field), song_edit=song_edit).save()
        if old_song.artist.name != edited_song.artist.name:
          FieldEdit(field="artist", new_value=edited_song.artist.name, song_edit=song_edit).save()
        if old_song.album.name != edited_song.album.name:
          FieldEdit(field="album", new_value=edited_song.album.name, song_edit=song_edit).save()

        messages.add_message(request, messages.SUCCESS, "Your edit has been queued for mod approval.")
  else:
    editform = SongForm(instance=song)

  commentform = CommentForm()
  comments = Comment.objects.select_related().filter(song=song)
  banform = BanForm()
  can_ban = request.user.has_perm('playlist.ban_song')
  if request.user.userprofile.canDelete(song):
    can_delete = True
  else:
    can_delete = False

  try:
    vote = Rating.objects.get(user=request.user, song=song).score
  except Rating.DoesNotExist:
    vote = 0
  if request.user.has_perm('playlist.edit_song') or request.user.has_perm('playlist.download_song'):
    path = song.getPath()
  else:
    path = None

  favourite = song in request.user.userprofile.favourites.all()

  # newsomnuke: get add history
  curadditions = PlaylistEntry.objects.select_related().filter(song__id=songid).order_by("-addtime");
  prevadditions = OldPlaylistEntry.objects.select_related().filter(song__id=songid).order_by("-addtime")

  addhistory = list(chain(curadditions, prevadditions))

  # get ratings and sort them into ascending order
  ratings = Rating.objects.select_related().filter(song__id=songid)
  ratings = sorted(ratings, key=lambda e: e.score)

  ratingsagg = {}
  for rating in ratings:
    trate = rating.score
    if trate in ratingsagg:
      ratingsagg[trate] += 1
    else:
      ratingsagg[trate] = 1

  return render(request, 'song.html', \
  {'song': song, 'editform':editform, 'edit':edit,'commentform':commentform,
  'currentuser':request.user, 'comments':comments, 'can_ban':can_ban,
  'banform':banform, 'can_delete':can_delete, 'vote':vote, 'path':path,
  'favourite':favourite, 'addhistory':addhistory, 'ratings':ratingsagg})

@permission_required("playlist.download_song")
def download_song(request, songid):
  try:
    song = Song.objects.get(id=songid)
  except:
    raise Http404

  response = HttpResponse(content_type="audio/mpeg")
  fsock = open(song.getPath(),"rb")
  response = HttpResponse(fsock, content_type="audio/mpeg")
  try:
    response['Content-Disposition'] = 'attachment; filename="' + song.title + "." + song.format + '"'
  except UnicodeEncodeError:
    #don't bother working around, just use the hash
    response['Content-Disposition'] = 'attachment; filename="' + song.sha_hash + "." + song.format + '"'
  print(song.getPath())
  return response

@login_required()
def album(request, albumid=None):
  try:
    album = Album.objects.select_related().get(id=albumid)
  except Album.DoesNotExist:
    raise Http404
  songs = album.songs.all().check_playable(request.user).select_related().order_by('track')
  return render(request, 'album.html', {'album': album, 'songs': songs})

@login_required()
def listartists(request, letter='123', page='1'):
  def the_filter(e):
    if len(e.name) > 4:
      return (not e.name[0].isalpha()) or (e.name[:4].lower() == "the" and (not e.name[4].isalpha()))
    elif len(e.name) == 0:
      return False
    else:
      return not e.name[0].isalpha()

  def sortkey(x):
    if len(x.name) > 4:
      return x.name[:4].lower()=="the " and x.name[4:].lower() or x.name.lower()
    else:
      return x.name.lower()
  letter = letter.lower()
  #artists = Artist.objects.all().order_by("name")

  #for artist in artists:
    #if artist.songs.count() == 0:
      #artist.delete() #prune empty artists

  if letter == '123':
    artists = Artist.objects.all().order_by("sort_name").annotate(song_count=Count('songs'))
    artists = filter(the_filter, artists)
  elif letter == "all":
    artists = Artist.objects.all().order_by("sort_name").annotate(song_count=Count('songs'))
  elif letter.isalpha():
    artists = Artist.objects.filter(sort_name__istartswith=letter).order_by("sort_name").annotate(song_count=Count('songs'))
  else:
    raise Http404
  #artists = list(artists)
  #artists.sort(key=sortkey) #sort 'the's properly
  try:
    page = int(page)
  except:
    page = 1
  p = Paginator(artists, 50)
  try:
    artists = p.page(page)
  except (EmptyPage, InvalidPage):
    #page no. out of range
    artists = p.page(p.num_pages)
  return render(request, 'artists.html', {"artists": artists, "letter": letter})


@permission_required('playlist.ban_song')
def bansong(request, songid=0):
  if request.method == "POST":
    form = BanForm(request.POST)
    if form.is_valid():
      song = Song.objects.get(id=songid)
      reason = form.cleaned_data['reason']
      song.ban(reason)
      song.save()
      logging.info("Mod %s (uid %d) banned songid %d with reason '%s' at %s" % (request.user.username, request.user.id, song.id, reason, now()))

  return HttpResponseRedirect(reverse('song', args=[songid]))

@permission_required('playlist.ban_song')
def unbansong(request, songid=0, plays=0):
  song = Song.objects.get(id=songid)
  song.unban(plays)
  logging.info("Mod %s (uid %d) unbanned songid %d for %d plays at %s" % (request.user.username, request.user.id, song.id, int(plays), now()))
  return HttpResponseRedirect(reverse('song', args=[songid]))

@login_required()
def deletesong(request, songid=0, confirm=None):
  """Deletes song with songid from db. Does not yet delete file."""
  try:
    song = Song.objects.get(id=songid)
  except Song.DoesNotExist:
    raise Http404

  if confirm != "yes":
    return render(request, "delete_confirm.html", {'song': song})

  if request.user.userprofile.canDelete(song):
    logging.info("User %s (uid %d) deleted song '%s' with hash %s at %s" % (request.user.username, request.user.id,
                                                                        song.metadataString(), song.sha_hash, now()))
    song.delete()
    return HttpResponseRedirect(reverse('playlist'))
  else:
    messages.add_message(request, messages.ERROR, "Error: you are not allowed to delete that song")
    return HttpResponseRedirect(reverse('song', args=[songid]))

@login_required()
def user(request, userid):
  try:
    owner=  User.objects.get(id=userid)
  except User.DoesNotExist:
    raise Http404

  # newsomnuke: get most recent additions, first from the current playlist, then from the playlist history
  curadditions = PlaylistEntry.objects.select_related().filter(adder=owner.id).order_by("-addtime")[:10];
  prevadditions = OldPlaylistEntry.objects.select_related().filter(adder=owner.id).order_by("-addtime")[:10]

  recentadds = list(chain(curadditions, prevadditions))[:10]

#  favouriteadds = Song.objects.select_related().annotate(totaladds = Count('oldentries')).order_by('-totaladds')[0:9]

  # recent uploads
  recentuploads = Song.objects.select_related().filter(uploader=owner.id).order_by("-add_date")[:10]

  # number of times the user's dongs have been added by other people
  curotheradds = PlaylistEntry.objects.select_related().filter(song__uploader__id=owner.id).exclude(adder__id=owner.id).count()
  otheradds = OldPlaylistEntry.objects.select_related().filter(song__uploader__id=owner.id).exclude(adder__id=owner.id).count() + curotheradds

  # number of dongs the user has added to the playlist
  curuseradds = PlaylistEntry.objects.select_related().filter(adder__id=owner.id).count()
  useradds = OldPlaylistEntry.objects.select_related().filter(adder__id=owner.id).count() + curuseradds

  # average score for uploaded dongs
  uploadavg = list(Song.objects.select_related().filter(uploader=owner.id).exclude(voteno=0).aggregate(Avg('avgscore')).values())[0]

  # number of comments written
  numcomments = Comment.objects.select_related().filter(user__id=owner.id).count()

  viewer = request.user.id
  return render(request, "user.html", \
  {'owner':owner, 'viewer':viewer, 'numcomments':numcomments, 'uploadavg':uploadavg, 'recentadds':recentadds,
  'recentuploads':recentuploads, 'otheradds':otheradds, 'useradds':useradds, 'token_button':request.user.has_perm("playlist.give_token")})

@permission_required("playlist.give_token")
def give_token(request, userid):
  try:
    profile = User.objects.get(id=userid).userprofile
  except User.DoesNotExist:
    raise Http404
  profile.tokens += 1
  profile.save()
  messages.add_message(request, messages.SUCCESS, "Token given successfully")
  return HttpResponseRedirect(reverse('user', args=[userid]))

@permission_required('playlist.can_comment')
def comment(request, songid):
  song = Song.objects.get(id=songid)
  if request.method == "POST":
    form = CommentForm(request.POST)
    if form.is_valid():
      #TODO: include song time
      song.comment(request.user, form.cleaned_data['comment'])
  return HttpResponseRedirect(reverse('song', args=[songid]))

@login_required()
def delete_comment(request, commentid):
  try:
    comment = Comment.objects.get(id=commentid)
  except:
    raise Http404
  if request.user.has_perm("playlist.delete_comment") or request.user == comment.user:
    comment.delete()
    messages.add_message(request, messages.SUCCESS, "Comment deleted successfully")
  else:
    messages.add_message(request, messages.ERROR, "You don't have permission to delete this comment")
  return HttpResponseRedirect(reverse('song', args=[comment.song.id]))

@permission_required('playlist.can_rate')
def rate(request, songid, vote):
  song = Song.objects.get(id=songid)
  song.rate(vote, request.user)
  return HttpResponseRedirect(reverse('song', args=[songid]))

@permission_required('playlist.upload_song')
def upload(request):
  if request.method == "POST":
    form = UploadFileForm(request.POST, request.FILES)
    if form.is_valid():
      f = request.FILES['file']
      try:
        request.user.userprofile.uploadSong(UploadedFile(f.temporary_file_path(), f.name))
      except DuplicateError:
        messages.add_message(request, messages.ERROR, "Error: track already uploaded")
      except FileTooBigError:
        messages.add_message(request, messages.ERROR, "Error: file too big")
      except StorageError:
        messages.add_message(request, messages.ERROR, "Error: file could not be stored!")
      else:
        messages.add_message(request, messages.ERROR, "Uploaded file successfully!")
  else:
    form = UploadFileForm()


  return render(request, 'upload.html', {'form': form})

# newsomnuke: added for global stats page
@login_required()
def globalstats(request):

  # SITE STATS
  # get total number of dongs in database
  totaldongs = Song.objects.count()

  # get total number of playlist adds
  curtotaladds = PlaylistEntry.objects.count()
  totaladds = OldPlaylistEntry.objects.count() + curtotaladds

  # get total number of unplayed dongs
  unplayeddongs = Song.objects.select_related().annotate(cnt=Count('oldentries')).exclude(cnt__gt=0).count()

  # get total number of registered users, maybe also 'active' users (added a dong in the last week)
  totalusers = UserProfile.objects.count()

  # DONG STATS
  # Get 10 most recent uploads
  recentuploads = Song.objects.select_related().order_by("-add_date")[:10]

  # Get 10 most popular dongs by playcount.  Technically we should check the current playlist as well as the playlist
  # history, but this is extra effort for a pretty minor issue, and the global stats page will likely take long enough
  # to load as it is.

  # this works, but is horrendously slow
  populardongs = Song.objects.select_related().annotate(totaladds=Count('oldentries')).order_by('-totaladds')[0:9]

  # do it directly with SQL
#  from django.db import connection
#  cursor = connection.cursor()
#  cursor.execute("SELECT COUNT(playlist_oldplaylistentry.song_id), playlist_song.title FROM playlist_oldplaylistentry, playlist_song WHERE (playlist_oldplaylistentry.song_id = playlist_song.id) GROUP BY playlist_oldplaylistentry.song_id ORDER BY count(playlist_oldplaylistentry.song_id) DESC LIMIT 0,10")

  # Get 10 most and least popular dongs by score, which have at least 10 votes
  votedhidongs = Song.objects.select_related().filter(voteno__gte=10).order_by("-avgscore")[:10]
  votedlodongs = Song.objects.select_related().filter(voteno__gte=10).order_by("avgscore")[:10]

  # TODO: get dong popularity by most 5s
#  dongmost5s = Rating.objects.select_related().annotate(fives=

  # TODO: get least popular dong by most 1s

  # ARTIST STATS
  # TODO: get most popular artist by playlist adds
  # TODO: get most popular artist by most 5s
  # TODO: get least popular artist by most 1s

  # USER STATS
  # TODO: get 10 users with most uploads
  # TODO: get 10 users with most adds
  # TODO: get 10 users with most reports/edits

  return render(request, 'stats.html', \
  {'recentuploads':recentuploads, 'populardongs':populardongs, 'votedhidongs':votedhidongs, 'votedlodongs':votedlodongs,
  'totaldongs':totaldongs, 'totaladds':totaladds, 'unplayeddongs':unplayeddongs, 'totalusers':totalusers})

@permission_required('playlist.view_artist')
def artist(request, artistid=None):
  try:
    artist = Artist.objects.get(id=artistid)
  except Artist.DoesNotExist:
    raise Http404
  print(artist)
  songs = Song.objects.select_related("artist", "album").check_playable(request.user).filter(artist=artist).order_by("album__name", "track")
  print(songs)
  return render(request, "artist.html", {'songs': songs, 'artist': artist})

@permission_required('playlist.queue_song')
def smart_add(request, category, user=None):
  if category == "unplayed":
    songs = Song.objects.annotate(entries_cnt=Count("entries")).filter(play_count=0, banned=False, entries_cnt=0)
  print(user)
  if user == "me":
    songs = songs.filter(uploader=request.user)
  elif user is not None:
    try:
      songs = songs.filter(uploader=User.objects.get(id=int(user)))
    except (ValueError, User.DoesNotExist, IndexError):
      raise Http404

  try:
    song = songs.order_by('?')[0]
  except IndexError:
    raise Http404
  return add(request, song.id)



@permission_required('playlist.queue_song')
def add(request, songid=None):
  """Add a song to the playlist, using a token if necessary or handling an error.
  Always leaves appropriate user message"""
  try:
    song = Song.objects.get(id=songid)
  except Song.DoesNotExist:
    raise Http404
  profile = request.user.userprofile
  oldtokens = profile.tokens
  try:
    song.playlistAdd(request.user)
  except AddError as e:
    msg = "Error: %s" % (e.args[0])
    messages.add_message(request, messages.ERROR, msg)
    return HttpResponseRedirect(reverse("playlist"))

  if oldtokens != profile.tokens:
      if profile.tokens:
        msg = "You already had a dong on the playlist, so you've used up a token to add this one. You have %d left" % (profile.tokens)
      else:
        msg = "You already had a dong on the playlist, so you've used up a token to add this one. That was your last one! (If you remove it, you'll get the token back though)"
      messages.add_message(request, messages.SUCCESS, msg)
  else:
    messages.add_message(request, messages.SUCCESS, "Track added successfully!")

  return HttpResponseRedirect(reverse("playlist"))

@never_cache
def next(request, authid):
  if authid == settings.NEXT_PASSWORD:
    try:
      entry = PlaylistEntry.objects.nowPlaying().next()
      location = entry.song.getPath()
      metadata = u"%s [blame %s]" % (entry.song.metadataString(request.user), entry.adder.username)
      entry.song.play_count += 1
      entry.song.save()
      return HttpResponse(location +'\n'+ metadata)
    except PlaylistEntry.DoesNotExist:
      pass
  return HttpResponse()

def newregister(request):
  get_authcode = lambda randcode: md5((settings.SECRET_KEY + randcode).encode('utf-8')).hexdigest()
  get_randcode = lambda: md5(str(getrandbits(64)).encode('utf-8')).hexdigest()
  error = ""
  if request.method == "POST":

    form = NewRegisterForm(request.POST)


    if form.is_valid():
      username = form.cleaned_data['saname']
      password = form.cleaned_data['password1']
      email = form.cleaned_data['email']
      authcode = get_authcode(form.cleaned_data['randcode'])
      error = None
      randcode = form.cleaned_data['randcode']

      if LIVE:
        try:
          profile = SAProfile(username)
        except URLError as e:
          error = "Couldn't find your profile. Check you haven't made a typo and that SA isn't down."
          #error = None

        try:
          if error is None and len(UserProfile.objects.filter(sa_id=profile.get_id())) > 0:
            error = "You appear to have already registered with this SA account"
        except IDNotFoundError:
          error = "Your SA ID could not be found. Please contact Jonnty"
          #error = None

        if error is None and not profile.has_authcode(authcode):
          error = "Verification code not found on your profile."
          #error = None

      if len(User.objects.filter(username__iexact=username)):
        error = "This username has already been taken. Please contact Jonnty to get a different one."

      if error is None:
        user = User.objects.create_user(username=username, email=email, password=password)
        try: g = Group.objects.get(name="Listener")
        except Group.DoesNotExist:
          g = Group(name="Listener")
          g.save()
          permissions = ["upload_song", "view_artist", "view_playlist", "view_song", "view_user", "queue_song"]
          [g.permissions.add(Permission.objects.get(codename=s)) for s in permissions]
          g.save()
        user.groups.add(g)
        user.save()
        up = UserProfile(user=user)
        #if LIVE:
        #  up.sa_id = profile.get_id()
        up.save()
        return HttpResponseRedirect(reverse("login"))
    else:
      randcode = request.POST['randcode']
  else:
    randcode = get_randcode()
    form = NewRegisterForm(initial={'randcode': randcode})
  authcode = get_authcode(randcode)
  return render(request, 'register.html', {'form': form, 'authcode': authcode, 'error':error})

@login_required()
def search(request):
  if request.method == 'GET' and "query" in request.GET: # If the form has been submitted...
    form = SearchForm(request.GET) # A form bound to the POST data
    if form.is_valid(): # All validation rules pass
      query = form.cleaned_data['query']

      artists = Artist.objects.select_related().filter(name__icontains=query).order_by('name')
      songs = Search(query).getResults().check_playable(request.user).order_by('title')
      albums = Album.objects.select_related().filter(name__icontains=query).order_by('name')

      paginator = Paginator(songs, 100)
      try: #sanity check
        page = int(request.GET.get('page', '1'))
      except ValueError:
        page = 1

      try: #range check
        songs = paginator.page(page)
      except (EmptyPage, InvalidPage):
        songs = paginator.page(paginator.num_pages)


      return render(request, 'search.html', {'form':form, 'artists':list(artists), 'albums':list(albums), 'songs':songs, 'query':query})

  else:
    form = SearchForm()
  return render(request, 'search.html', {'form':form})
