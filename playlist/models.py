#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db import models
from playlist import utils
import datetime
import os
import errno
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from django.contrib.auth.models import User

from django.conf import settings
from django.db.models.signals import pre_save
from django.db.models import Avg, Count, Sum
from django.db.models.query import QuerySet
from playlist.utils import getObj, try_read
from playlist.cue import CueFile
from django.template.defaultfilters import safe, force_escape
from django.utils import timezone




class DuplicateError(Exception): pass
class ScoreOutOfRangeError(Exception): pass
class AddError(Exception): pass
class FileTooBigError(Exception): pass
class SongPlayingError(Exception): pass
class CommentTooLongError(Exception): pass
class StorageError(Exception): pass


class Artist(models.Model):
  name = models.CharField(max_length=255, unique=True)
  sort_name = models.CharField(max_length=300)

  def __str__(self):
    return str(self.name)

  #maybe url, statistics?

  #playlist.Artist: (auth.E005) The permission codenamed 'view_artist' clashes with a builtin permission for model 'playlist.Artist'.
  # class Meta:
  #   permissions = (
  #   ("view_artist",  "g2 Can view artist pages."),
  #   )
  #def save(self):
    ##clean up name and change sort_name
    #self.name = self.name.strip()
    #if len(self.name) > 4:
      #self.sort_name = self.name[:4].lower()=="the " and self.name[4:] or self.name
    #else:
      #self.sort_name = self.name
    #self.sort_name = self.sort_name.lstrip("'\"")

    #super(Artist, self).save()

def artist_handler(sender, **kwargs):
  instance = kwargs['instance']
  #clean up name and change sort_name
  instance.name = instance.name.strip()
  instance.sort_name = instance.name.lstrip("'\"")
  if len(instance.name) > 4:
    instance.sort_name = instance.sort_name[:4].lower()=="the " and instance.sort_name[4:] or instance.sort_name
  else:
    instance.sort_name = instance.sort_name

def dupe_handler(sender, **kwargs):
  instance = kwargs['instance']
  for dupe in sender.objects.filter(name=instance.name):
    for song in dupe.songs.all():
      instance.songs.add(song)
    dupe.delete()


pre_save.connect(artist_handler, sender=Artist)
#pre_save.connect(dupe_handler, sender=Artist)

class Album(models.Model):
  name = models.CharField(max_length=255, unique=True)
  def __str__(self):
    return str(self.name)

class Rating(models.Model):
  score = models.FloatField()
  user = models.ForeignKey(User, related_name='ratings', on_delete=models.CASCADE)
  song = models.ForeignKey('Song', related_name='ratings', on_delete=models.CASCADE)

  def __str__(self):
    return str(self.score)

  class Meta:
    unique_together = ('user', 'song')
    permissions = (
    ("can_rate",  "g2 Can rate songs"),
    )

class UserProfile(models.Model):
  user = models.OneToOneField(User,  unique=True, on_delete=models.CASCADE)
  uploads = models.IntegerField(default=0)
  #last_ip = models.CharField(max_length=15)
  api_key = models.CharField(max_length=40, editable=False, blank=True)
  sa_id = models.IntegerField(blank=True, null=True, unique=True,
                              help_text="Something Awful account ID")
  favourites = models.ManyToManyField("Song", related_name="lovers", blank=True)
  tokens = models.IntegerField(default=0)

  #settings
  s_playlistHistory = models.IntegerField(default=10, help_text="Number of previously played dongs shown")

  def __unicode__(self): return self.name


  def uploadSong(self, upload):
    """Add an UploadedSong to the database if allowed"""
    if not self.user.has_perm("playlist.upload_song"):
      return #do nothing while cackling quietly
    try:
      Song.objects.get(sha_hash=upload.info['sha_hash'])
    except Song.DoesNotExist:
      pass
    else:
      raise DuplicateError("song already in database")

    if os.path.getsize(upload.file) > settings.MAX_UPLOAD_SIZE:
      raise FileTooBigError

    upload.info['uploader'] = self.user
    s = upload.store()

    if s.length > settings.MAX_SONG_LENGTH: #11 mins
      s.ban("Autobahned because the dong is too long. Ask a mod to unban it if you want to play it.")
    s.save()

    self.user.userprofile.uploads += 1
    self.user.save()
    return s.id

  def addDisallowed(self, entries=None):
    #check user hasn't got too many songs on the playlist
    if not entries: #can be passed in for database efficiency
      entries = PlaylistEntry.objects.all()

    entrycount = len(entries.filter(adder=self.user))
    try:
      if PlaylistEntry.objects.nowPlaying().adder == self.user:
        entrycount -= 1 #don't count it if it's currently playing
    except PlaylistEntry.DoesNotExist:
      pass #no song's playing, doesn't matter
    if entrycount >= int(settings.PLAYLIST_MAX):
      return ("you already have too many songs on the playlist", "user is greedy")
    else:
      return None #no reason to disallow add based on user activities

  def _getSongInfo(self,  file):
    """Returns dict with tags and stuff"""
    d = {}
    song = MP3(file.temporary_file_path(), ID3=EasyID3)
    d.update(song)

    for value in d.keys():
      d[value] = d[value][0] #1-string list -> string

    d['length'] = round(song.info.length)
    d['bitrate'] = song.info.bitrate/1000 #b/s -> kb/s
    #d['filesize'] = file.size

    if not ("title" in d.keys()):
      d['title'] = file.name
    if 'artist' in d.keys():
      d['artist'] = utils.getObj(Artist, d['artist'])
    else:
      d['artist'] = utils.getObj(Artist, "unknown")
    if 'album' in d.keys():
      d['album'] = utils.getObj(Album, d['album'])
    else:
      d['album'] = utils.getObj(Album, "unknown")

    for x in ["tracknumber", "version", "date"]:
      if x in d.keys():
        del d[x]

    d['format'] = "mp3"

    return d

  def canDelete(self, song):
    if self.user.has_perm('playlist.delete_song'):
      return True
    if PlaylistEntry.objects.filter(song=song) or OldPlaylistEntry.objects.filter(song=song):
      return False #on playlist
    td = datetime.timedelta(days=1)
    #now = datetime.datetime.now()
    now = timezone.now()
    if (now < song.add_date+td) and (self.user == song.uploader):
      return True
    return False

  #def _getObj(self, name, table):
    #"""get object if it exists; otherwise create it"""
    #try:
      #return table.objects.get(name=name)
    #except:
      #t = table(name=name)
      #t.save()
      #return t
      #def __unicode__(self): return unicode(self.id)

  class Meta:
    permissions = (
    ("view_user",  "g2 Can view user pages"),
    ("give_token",  "g2 Can award tokens to users"),
    )

  def __unicode__(self): return self.user.username


class SongSet(QuerySet):
  """Extends QuerySet for aggregated song checking methods"""

#  def __init__(self, model=None):
#    super(SongSet, self).__init__(model)

  def check_playable(self, user):

    #song already on playlist
    playlist = 'SELECT COUNT(*) FROM playlist_playlistentry \
            WHERE playlist_playlistentry.song_id = playlist_song.id'

    #song too recently played
    recent = '(SELECT count(*) FROM playlist_oldplaylistentry \
              WHERE (playlist_oldplaylistentry.song_id = playlist_song.id) AND \
              (playlist_oldplaylistentry.playtime-0 > NOW()-INTERVAL %d HOUR))' % (settings.REPLAY_INTERVAL)

    select = {#'is_banned' : 'banned = 1',
              #'on_playlist' : playlist,
              'recently_played': recent,
              }
    return super(SongSet, self).annotate(on_playlist=Count('entries')).\
                                          extra(select=select)

class SongManager(models.Manager):
  def get_queryset(self):
    return SongSet(self.model)  #force Song to use extended queryset


class EditNote(models.Model):
  """Note which mods can add to SongEdits to explain their actions or (more likely) make poor jokes"""
  author = models.ForeignKey(User, related_name="edit_notes", on_delete=models.CASCADE)
  edit = models.ForeignKey("SongEdit", related_name="notes", on_delete=models.CASCADE)
  note = models.CharField(max_length=300)

class FieldEdit(models.Model):
  """Represents an edit to a single field"""
  new_value = models.CharField(max_length=300, blank=False)
  field = models.CharField(max_length=50, blank=False)
  song_edit = models.ForeignKey("SongEdit", related_name="field_edits", on_delete=models.CASCADE)

class SongEdit(models.Model):
  """Represents an edit to a song made by an unprivilidged user which needs mod approval"""
  requester = models.ForeignKey(User, related_name="requested_edits", on_delete=models.CASCADE)
  applied = models.BooleanField(default=False)
  denied = models.BooleanField(default=False)
  actioned_by = models.ForeignKey(User, related_name="actioned_edits", null=True, blank=True, on_delete=models.CASCADE)
  created_at = models.DateTimeField()
  actioned_at = models.DateTimeField(null=True, default=None)
  song = models.ForeignKey("Song", related_name="requested_edits", on_delete=models.CASCADE)

  def deny(self, denier):
    if not self.denied or self.applied:
      self.denied = True
      self.actioned_by = denier
      self.actioned_at = datetime.datetime.today()
      self.save()

  def apply(self, applier):
    """Apply this edit to the song to which it is attached, setting it as applied by applier"""
    if not (self.applied or self.denied):
      for edit in self.field_edits.all():
        if edit.field == "artist":
          self.song.artist = getObj(Artist, edit.new_value)
        elif edit.field == "album":
          self.song.album = getObj(Album, edit.new_value)
        else:
          setattr(self.song, edit.field, edit.new_value)

      self.song.save()
      self.applied = True
      self.actioned_by = applier
      self.actioned_at = datetime.datetime.today()
      self.save()

  def add_note(self, author, note):
    EditNote(author=author, note=note, edit=self).save()

  def save(self):
    #ensure datetime is creation date
    if not self.id:
        self.created_at = datetime.datetime.today()
    super(SongEdit, self).save()

  class Meta:
    permissions = (
    ("view_edits",  "g2 Can view & approve/deny SongEdits"),
    )

class SongReport(models.Model):
  song = models.ForeignKey("Song", related_name="reports", editable=False, null=True, on_delete=models.CASCADE)
  reporter = models.ForeignKey(User, related_name="song_reports", editable=False, on_delete=models.CASCADE)
  #reasons
  corrupt = models.BooleanField(default=False)
  not_music = models.BooleanField(default=False)
  other = models.BooleanField(default=False)
  duplicate = models.ForeignKey("Song", null=True, on_delete=models.CASCADE)

  user_note = models.CharField(max_length=300, blank=True)

  created_at = models.DateTimeField()
  actioned_at = models.DateTimeField(null=True)
  actioned_by = models.ForeignKey(User, related_name="actioned_song_reports", null=True, on_delete=models.CASCADE)
  approved = models.BooleanField(default=False)
  denied = models.BooleanField(default=False)

  def approve(self, actioner):
    """Approve the report, taking any necessary action"""
    if self.denied: return
    self.actioned_at = datetime.datetime.today()
    self.actioned_by = actioner
    self.approved = True
    self.save()

    if self.duplicate:
      #asume songid exists: earlier checks should be made
      dupe = self.duplicate
      song = self.song
      self.song = None
      self.save() #avoid cascaded deletion
      dupe.merge(song)
      return #song has gone!

    if self.corrupt:
      #delete song
      self.song.delete()
      return #song has gone!

    if self.not_music:
      self.song.ban("This dong is not music.")

  def deny(self, actioner):
    """Deny the report"""
    if self.approved: return

    self.actioned_at = datetime.datetime.today()
    self.actioned_by = actioner
    self.denied = True
    self.save()


  def save(self):
    #ensure datetime is creation date
    if not self.id:
        self.created_at = datetime.datetime.today()
    super(SongReport, self).save()

  class Meta:
    permissions = (
    ("approve_reports",  "g2 Can view & approve/deny SongEdits"),
    )

class Song(models.Model):
  """Represents a song, containing all tags and other metadata"""
    #TODO: sort out artist/composer/lyricist/remixer stuff as per note
  title = models.CharField(max_length=300)
  artist = models.ForeignKey(Artist, blank=True, related_name='songs', on_delete=models.CASCADE)
  album = models.ForeignKey(Album, blank=True, related_name='songs', on_delete=models.CASCADE)
  composer = models.CharField(max_length=300, blank=True) #balthcat <3
  lyricist = models.CharField(max_length=300, blank=True)
  remixer = models.CharField(max_length=300, blank=True) #balthcat <3
  genre = models.CharField(max_length=100, blank=True)
  track = models.PositiveIntegerField(blank=True, null=True)
  length = models.IntegerField(editable=False) #in seconds
  bitrate = models.IntegerField(editable=False) #in kbps
  sha_hash = models.CharField(max_length=40, unique=True, editable=False)
  add_date = models.DateTimeField(editable=False)
  format = models.CharField(max_length=5, editable=False)
  uploader = models.ForeignKey(User, editable=False, related_name="uploads", on_delete=models.CASCADE)
  category = models.CharField(max_length=20, default="regular", editable=False)

  banned = models.BooleanField(default=False, editable=False)
  banreason = models.CharField(max_length=100, blank=True, editable=False)
  unban_adds = models.IntegerField(default=0, editable=False) #number of plays till rebanned: 0 is forever

  location = models.ForeignKey("SongDir", null=True, editable=False, on_delete=models.CASCADE)

  avgscore = models.FloatField(default=0, editable=False)
  voteno = models.IntegerField(default=0, editable=False)
  play_count = models.IntegerField(default=0, editable=False) #finally!
  # ratings, comments, entries & oldentries are related_names



  objects = SongManager()
  #stream_options = StreamOptions()

  def addDisallowed(self):
    """Returns (reason, shortreason) tuple.
    Reason for user, shortreason for add button.
    More effcient & comprehensive if called on queryset returned from check_playable
    Otherwise returns False.
    """
    try:
      if self.on_playlist:
         return ("song already on playlist", "on playlist")
      if self.recently_played:
        return ("song played too recently", "recently played")
      if self.banned:
        return ("song banned", "banned")
#      elif self.greedy_user:
#        return ("you already have too many songs on the playlist", "user is greedy")
    except:
      if self.banned:
        return ("song banned", "banned")
      if len(PlaylistEntry.objects.filter(song=self)) > 0:
        return ("song already on playlist", "on playlist")
      #check song hasn't been played recently: dt is definition of 'recently'
      dt = datetime.datetime.now()-datetime.timedelta(hours=int(settings.REPLAY_INTERVAL))
      if len(OldPlaylistEntry.objects.filter(song=self, playtime__gt=dt)) > 0:
        return ("song played too recently", "recently played")

    return False

  def playlistAdd(self,  user):
    """Adds song to the playlist. Silently use up a token if necessary.
    Raises AddError if there's a problem, with (reason, shortreason) as its arg."""

    reasons = self.addDisallowed() #check song can be added
    if reasons:
      reason, shortreason = reasons
      raise AddError(reason, shortreason)
    profile = user.userprofile
    reasons = profile.addDisallowed() #check user can add
    token_used = False
    if reasons:
      reason, shortreason = reasons
      if shortreason == "user is greedy" and profile.tokens:
        #extra add, use up a token
        profile.tokens -= 1
        token_used = True
        profile.save()
      else:
        raise AddError(reason, shortreason)
    if self.unban_adds:
      self.unban_adds -= 1
      if self.unban_adds == 0:
        self.ban() #assume reason already there
      self.save()
    p = PlaylistEntry(song=self, adder=user)
    p.token_used = token_used
    if len(PlaylistEntry.objects.filter(playing=True)) == 0: #no song playing - use this one
      p.playing=True
      p.playtime = datetime.datetime.today()

    p.save()

  def __unicode__(self): return self.artist.name + ' - ' + self.title

  def getPath(self):
    return self.location.genPath(self.sha_hash, self.format)

  def ban(self, reason=""):
    self.banned = True
    if reason:
      self.banreason = reason
    self.save()

  def unban(self, plays=0):
    self.banned = False
    self.unban_adds = plays
    self.save()

  def metadataString(self, user=None):
    #TODO: implement user customisable format strings & typed strings
    if self.category == 'regular':
      return u"%s (%s) - %s" % (self.artist, self.album, self.title)

  def rate(self, score, user):
    score = float(score)
    if not ((1 <= score and score <= 5) or (score==0)):
      raise ScoreOutOfRangeError

    try:
      r = Rating.objects.get(user=user, song=self)
      prevscore = r.score
      if score == 0: #0 is delete
        r.delete()
      else:
        r.score = score
        r.save()
    except Rating.DoesNotExist:
      #not yet created (yes I know this is what get_or_create is for but it's stupid
      #(it can't do required fields properly))
      prevscore = 0
      if score != 0: #0 is delete, don't create instead
        r = Rating(user=user, song=self, score=score)
        r.save()
    #sort out statistics
    stats = Rating.objects.filter(song=self).aggregate(id_count=Count('id'), avg_score=Avg('score'))
    if (not stats['id_count']) or (not stats['avg_score']):
      self.voteno = self.avgscore = 0
    else:
      self.voteno = stats['id_count'] #Rating.objects.filter(song=self).count()
      #ratings = [rating['score'] for rating in Rating.objects.filter(song=self).values()]
      self.avgscore = stats['avg_score'] #sum(ratings) / self.voteno
    self.save()
    return prevscore

  def comment(self, user, comment):

    if PlaylistEntry.objects.nowPlaying().song == self:
      #cue = CueFile(settings.LOGIC_DIR + "/ices.cue")
      cue = CueFile("/remaining/ices2.cue")
      time = cue.getTime(self)
    else:
      time = 0
    c = Comment(text=comment, user=user, song=self, time=time)
    c.save()
    return time #for API


  def getOldPlayCount(self):
    return OldPlaylistEntry.objects.filter(song=self).count()

  def getPlayCount(self):
    return self.play_count

  def merge(self, song):
    """
    Merge song into this one, copying all relevent metadata (like comments and votes)
    then deleting it.
    """
    if PlaylistEntry.objects.nowPlaying().song == song:
      raise SongPlayingError("song merged is playing at the moment")
    for comment in song.comments.all():
      self.comments.add(comment)

    users = [rating.user for rating in self.ratings.all()]
    for rating in song.ratings.all():
      #ensure people who've voted on both songs only get one vote counted
      if rating.user not in users:
        self.ratings.add(rating)
    #sort out statistics
    stats = self.ratings.all().aggregate(id_count=Count('id'), avg_score=Avg('score'))
    if (not stats['id_count']) or (not stats['avg_score']):
      self.voteno = self.avgscore = 0
    else:
      self.voteno = stats['id_count']
      self.avgscore = stats['avg_score']

    for entry in song.oldentries.all():
      entry.song = self
      entry.save()

    for entry in song.entries.all():
      entry.song = self
      entry.save()

    #steal old song's tags where this one lacks them
    #MUST BE UPDATED IF/WHEN NEW TAGS ADDED (sorry code nazis)
    for tag in ['title', 'artist', 'album', 'composer', 'lyricist', 'remixer', 'genre', 'track']:
      if not getattr(self, tag) and getattr(song, tag):
        setattr(self, tag, getattr(song, tag))

    song.delete()
    self.save()


  def save(self):
    #ensure add_date is creation date
    if not self.id:
        self.add_date = datetime.datetime.today()
    super(Song, self).save()

  def delete(self):
    #prune artist if now empty
    if self.artist.songs.count() <= 1:
        self.artist.delete()
    super(Song, self).delete()



  class Meta:
    permissions = (
    # ("view_song",  "g2 Can view song pages"), playlist.Song: (auth.E005) The permission codenamed 'view_song' clashes with a builtin permission for model 'playlist.Song'.
    ("upload_song",  "g2 Can upload songs"),
    ("ban_song",  "g2 Can ban songs"),
    ("edit_song", "g2 Can edit all songs."),
    ("start_stream", "g2 Can start the stream."),
    ("stop_stream", "g2 Can stop the stream"),
    ("view_g2admin", "g2 Can view g2 Admin page."),
    ("download_song", "g2 Can download songs directly from the server"),
    ("merge_song", "g2 Can merge one song into another")
    )


class SongDirManager(models.Manager):


  def getUsableDir(self):
    """Return the first directory object we can find that's usable"""
    try:
      return super(SongDirManager, self).filter(usable=True)[0]
    except IndexError:
      raise StorageError("there are no usable directories available for storage")


class SongDir(models.Model):
  """Represents a directory for storing song files in"""
  #absolute path to directory
  path = models.CharField(max_length=300)
  #number of letters of file hash to use for subdirectories. 0 means no subdirectories
  hash_letters = models.IntegerField()
  #True if accepting new uploads
  usable = models.BooleanField(default=True)

  objects = SongDirManager()

  def _create_dir_if_neccessary(self, path):
    try:
      os.makedirs(path)
    except OSError as e:
      if e.errno != errno.EEXIST:
        raise

  def storeSong(self, temp_path, info):
    new_file = open(self.genPath(info['sha_hash'], info['format']),  'wb', True)
    temp_file = open(temp_path, 'rb')

    try:
      new_file.write(temp_file.read())
    finally:
      temp_file.close() #temp file so no need to delete
      new_file.close()

  def genPath(self, sha_hash, format, create_if_necessary=False):
    hash_dir = sha_hash[0:self.hash_letters] #get appripriate number of hash digits
    dir_path = self.path+'/'+ hash_dir
    if create_if_necessary:
      self._create_dir_if_neccessary(dir_path)
    return dir_path + '/' + sha_hash + '.' + format

  def __unicode__(self):
    if self.usable:
      return str(self.path) + " (Usable)"
    else:
      return str(self.path) + " (Not Usable)"

class Emoticon(models.Model):
  text = models.CharField(max_length=100)
  alt_text = models.CharField(max_length=100)
  filename = models.CharField(max_length=100)
  usable = models.BooleanField(default=True)
  cripple = models.BooleanField(default=False)

  def __unicode__(self):
    if self.usable:
      return self.text
    else:
      return self.text + " (disabled)"


class Comment(models.Model):
  text = models.CharField(max_length=4000)
  user = models.ForeignKey(User, editable=False, related_name="comments", on_delete=models.CASCADE)
  song = models.ForeignKey(Song, editable=False, related_name="comments", on_delete=models.CASCADE)
  time = models.IntegerField(default=0)
  datetime = models.DateTimeField()

  def save(self, *args, **kwargs):
    #ensure datetime is creation date
    if not self.id:
        self.datetime = datetime.datetime.today()

    if len(self.text) > 400:
      raise CommentTooLongError("comment must be less than 400 characters")

    self.text = self._add_emoticons(self.text)
    super(Comment, self).save(*args, **kwargs)

  def _add_emoticons(self, text):
    text = force_escape(text)
    text = text.split()
    emoticons = Emoticon.objects.filter(text__in=text)
    for i, word in enumerate(text):
      for e in emoticons:
        if e.text == word:
          text[i] = "<img src='%s' alt='%s' title='%s' />" % (
            "emoticons/"+e.filename,
            e.alt_text,
            e.text
          )
          break
    return " ".join(text)


  def ajaxEvent(self):
    """
    Return event to be sent to client on ajax request for comments.
    """
    html_title = "Made on %s" % self.datetime.strftime("%d %b %Y")
    details = {
      'body': self.text,
      'time': self.datetime.strftime("%H:%M"),
      'html_title': html_title,
      'commenter': self.user.username,
      'id': self.id
    }
    return ('comment', details)

  class Meta:
    ordering = ['-datetime']
    permissions = (
    ("can_comment",  "g2 Can comment on songs"),
    )


class PlaylistManager(models.Manager):

  def length(self):
    """Returns dictionary of playlist length in seconds and song count."""
    return super(PlaylistManager, self).select_related('song').filter(playing=False).aggregate(seconds=Sum('song__length'), song_count=Count('song'))

  def nowPlaying(self):
    return super(PlaylistManager, self).select_related().get(playing=True)


class PlaylistEntry(models.Model):

  song = models.ForeignKey(Song, related_name="entries", on_delete=models.CASCADE)
  adder = models.ForeignKey(User, on_delete=models.CASCADE)
  addtime = models.DateTimeField()
  playtime = models.DateTimeField(null=True, blank=True)
  playing = models.BooleanField(default=False)
  hijack = models.BooleanField(default=False)
  token_used = models.BooleanField(default=False) #was this song added with a token?

  def next(self):
    try:
      #set up new entry
      new = PlaylistEntry.objects.exclude(id=self.id)[0]
    except IndexError:
      #no more songs :(
      #oh well, repeat this one and *don't* record it as having played
      #old = OldPlaylistEntry(song=self.song, adder=self.adder, addtime=self.addtime, playtime=self.playtime)
      #old.save()
      #self.playtime=datetime.datetime.today()
      return self

    new.playing = True
    new.playtime = datetime.datetime.today()
    #record old one
    old = OldPlaylistEntry(song=self.song, adder=self.adder, addtime=self.addtime, playtime=self.playtime)
    old.save()
    self.delete()
    new.save()
    return new

  def remove(self):
    """removes from playlist and lets ajax playlist handler know"""
    RemovedEntry(oldid=self.id).save()
    if self.token_used:
      p = self.adder.userprofile
      p.tokens += 1 #return token
      p.save()
    self.delete()

  def save(self):
    if not self.id:
        self.addtime = datetime.datetime.today()
    super(PlaylistEntry, self).save()

  def __unicode__(self): return self.song.title

  def delSong(self, songid):
    self.entries.objects.get(id=songid).delete()
    self.save()

  objects = PlaylistManager()

  class Meta:
    ordering = ['-playing', '-hijack', 'addtime']
    permissions = (
    ("view_playlist",  "g2 Can view the playlist"),
    ("queue_song",  "g2 Can add song to the playlist"), #golden_appel <3
    ("remove_entry", "g2 Can remove all playlist entries"),
    ("skip_song", "g2 Can skip currently playing song")
    )
    verbose_name_plural = "Playlist"

class RemovedEntry(models.Model):
  oldid = models.IntegerField()
  creation_date = models.DateTimeField()

  def save(self):
    if not self.id: #populate creation date
        self.creation_date = datetime.datetime.today()
    super(RemovedEntry, self).save()

class OldPlaylistEntry(models.Model):
  song = models.ForeignKey(Song, related_name="oldentries", on_delete=models.CASCADE)
  adder = models.ForeignKey(User, on_delete=models.CASCADE)
  addtime = models.DateTimeField()
  playtime = models.DateTimeField()
  skipped = models.BooleanField(default=False)

  class Meta:
    ordering = ['id']

class Settings(models.Model):
  key = models.CharField(max_length=200)
  value = models.CharField(max_length=3000)

  def __unicode__(self): return self.key

  class Meta:
    ordering = ['key']


####### DJ Shows ########

class Series(models.Model):
  name = models.CharField(max_length=200)
  short_name = models.CharField(max_length=15)
  description = models.CharField(max_length=2500)

  def __unicode__(): unicode(short_name)

class Show(models.Model):
  """A DJ show scheduled for the future"""
  start_time = models.DateTimeField()
  end_time = models.DateTimeField()
  owner = models.ForeignKey(User, related_name="shows", on_delete=models.CASCADE)
  name = models.CharField(max_length=200)
  description = models.CharField(max_length=2500)
  reschedule = models.BooleanField()
  series = Series

class OldShow(models.Model):
  """Recorded show. Also used for current shows"""
  start_time = models.DateTimeField(blank=True, null=True)
  end_time = models.DateTimeField(blank=True, null=True)
  owner = models.ForeignKey(User, related_name="oldshows", on_delete=models.CASCADE)
  name = models.CharField(max_length=200)
  description = models.CharField(max_length=2500)
  playing = models.BooleanField(default=True)

class ShowRating(models.Model):
  score = models.FloatField()
  user = models.ForeignKey(User, related_name='show_ratings', on_delete=models.CASCADE)
  show = models.ForeignKey(OldShow, related_name='ratings', on_delete=models.CASCADE)

  def __unicode__(self): return unicode(self.rating)

  class Meta:
    unique_together = ('user', 'show')


class ShowComment(models.Model):
  text = models.CharField(max_length=400)
  user = models.ForeignKey(User, editable=False, related_name="show_comments", on_delete=models.CASCADE)
  show = models.ForeignKey(OldShow, editable=False, related_name="comments", on_delete=models.CASCADE)
  time = models.DateTimeField()

  def save(self):
    #ensure datetime is creation date
    if not self.id:
        self.datetime = datetime.datetime.today()
    super(Comment, self).save()
  class Meta:
    ordering = ['-time']

class ShowMinute(models.Model):
  """Minutely recording of various show statistics"""
  show = models.ForeignKey(OldShow, related_name="minutes", on_delete=models.CASCADE)
  time = models.DateTimeField()
  listeners = models.IntegerField()
  metadata = models.CharField(max_length=300)
  avg_score = models.FloatField()


def randomdongid():
    from django.db import connection
    cursor = connection.cursor()

    # Data retrieval operation - no commit required
    cursor.execute("SELECT * from public_data.random_dongid")
    row = cursor.fetchone()

    return row

def plinfoq(self):
    from django.db import connection
    cursor = connection.cursor()

    # Data retrieval operation - no commit required
    cursor.execute("select song.id, song.title, artist.name, album.name from playlist_song song, playlist_artist artist, playlist_album album where song.artist_id = artist.id and song.album_id = album.id and song.id = (SELECT song_id FROM `gbsfm`.`playlist_playlistentry` order by id limit %s,1)", [int(self)])
    row = cursor.fetchone()
    return row
