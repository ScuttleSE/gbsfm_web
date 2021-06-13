# -*- coding: utf-8 -*-
import sys
import os.path
from mutagen import File
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.oggopus import OggOpus
from mutagen.easymp4 import EasyMP4
from mutagen.mp3 import HeaderNotFoundError
import hashlib

from playlist.models import *
from django.contrib.auth.models import User

class UnsupportedFormatError(Exception): pass
class CorruptFileError(Exception): pass

class UploadedFile:
  supported_types = ['mp3', 'flac', 'mp4', 'm4a', 'ogg', 'webm', 'vqf', 'mp2'] #TODO: make this a config option for god's sake
  def __init__(self, file, realname=None, filetype=None):
    
    self.type = filetype
    
    if realname is None:
      realname = os.path.basename(file)
    self.realname = realname
    
    if self.type is None:
      self.type = os.path.splitext(realname)[1].strip('.')
      
    self.type = self.type.lower()  
    
    if self.type not in self.supported_types:
      if not self.type:
        raise UnsupportedFormatError, "Could not detect filetype"
      else:
        raise UnsupportedFormatError, "%s not supported" % self.type
    
    self.info = {}
    self.file = file
    self.getHash()
    self.getTags()
    
    
    
  def getHash(self):
    """Populates self.sha_hash with sha1 hash of uploaded file."""
    f = open(self.file)
    self.info['sha_hash'] = hashlib.sha1(f.read()).hexdigest()
    f.close()
    
  def store(self):
    """Store song in a usable directory using SongDir
    and record it in the database. Return the Song object created."""
    storage = SongDir.objects.getUsableDir()
    storage.storeSong(self.file, self.info)
    self.info['location'] = storage #make sure song knows where it is stored
    s = Song(**self.info) 
    s.save()
    return s
  
  def getTags(self):
    """Run correct tagging method. 
    
    Method name format: _get<type in uppercase>Tags"""
    getattr(self, '_fill'+self.type.upper()+'Tags')()
  
  def _get(self, song, key, default):
    """Returns the value for key in song, replacing it with default if necessary
    and removing it from list."""
	if not song:
		return default
    value = song.get(key, default)
    try:
      value = value[0]
    except (IndexError, TypeError):
      pass #value is empty list/isn't stored in list
    if value:
      return value
    else:
      #value empty
      return default
  
  def _fillMP3Tags(self):
    """Returns dict with tags and stuff"""
    tags = {}
    
    try:
      song = MP3(self.file, ID3=EasyID3)
    except HeaderNotFoundError:
      raise CorruptFileError

    tags = {}
    tags['length'] = round(song.info.length)
    tags['bitrate'] = song.info.bitrate/1000 #b/s -> kb/s
    tags['format'] = "mp3"
    self.info.update(tags)
    
    self._fillInfoTags(song)
 
  def _fillFLACTags(self):
    """Returns dict with tags and stuff"""
    tags = {}
    
    try:
      song = FLAC(self.file)
    except HeaderNotFoundError:
      raise CorruptFileError
    
    
    tags = {}
    tags['length'] = round(song.info.length)
    tags['bitrate'] = (os.path.getsize(song.filename)/song.info.length)/1000 #b/s -> kb/s
    tags['format'] = "flac"
    self.info.update(tags)
    
    self._fillInfoTags(song)
    
  
  def _fillM4ATags(self):
    self._fillMP4Tags() #same format
    self.info["format"] = "m4a" #avoid confusion
  
  def _fillMP4Tags(self):
    """Returns dict with tags and stuff"""
    try:
      song = EasyMP4(self.file)
    except HeaderNotFoundError:
      raise CorruptFileError
    
    tags = {}
    tags['length'] = round(song.info.length)
    tags['bitrate'] = song.info.bitrate/1000 #b/s -> kb/s
    tags['format'] = "mp4"
    self.info.update(tags)
    
    self._fillInfoTags(song)
    
    
  def _fillOGGTags(self):
    """Returns dict with tags and stuff"""
    try:
      song = OggVorbis(self.file)
    except HeaderNotFoundError:
      raise CorruptFileError
    
    tags = {}
    tags['length'] = round(song.info.length)
    tags['bitrate'] = song.info.bitrate/1000 #b/s -> kb/s
    tags['format'] = "ogg"
    self.info.update(tags)
    
    self._fillInfoTags(song)

  def _fillWEBMTags(self):
    # No mutagen support
    tags = {}
    tags['format'] = "opus"
    self.info.update(tags)
    self._fillInfoTags(None)


  def _fillVQFTags(self):
    # No mutagen support
    tags = {}
    tags['format'] = "vqf"
    self.info.update(tags)
    self._fillInfoTags(None)


  def _fillMP2Tags(self):
    # No mutagen support
    tags = {}
    tags['format'] = "mp2"
    self.info.update(tags) 
    self._fillInfoTags(None)


  def _fillInfoTags(self, song):
    """Fill the main bulk of tags, like title, artist etc, which are generally uniform
    across formats"""
    
    tags = {}
    tags['title'] = self._get(song, 'title', self.realname) #use filename as default 
    artist = self._get(song, 'artist', '(unknown')
    album  = self._get(song, 'album', '(unknown')
    tags['artist'] = Artist.objects.get_or_create(name=artist)[0]
    tags['album'] = Album.objects.get_or_create(name=album)[0]  
    tags['genre'], tags['composer'] = self._get(song, 'genre', ""), self._get(song, 'composer', "")
    
    track = self._get(song, 'tracknumber', 0)
    try:
      tags['track'] = int(track)
    except ValueError:
      #handle tracknumbers like 11/12 meaning 'track eleven of twelve'
      #basically just extract the initial int
      tags['track'] = ""
      for char in track:
        try:
          tags['track'] += str(int(char))
        except ValueError:
          break

    #Try converting tracks like A1 B2 etc to int
    try:
      if 'track' not in tags or tags['track'] is None:
        tags['track'] = int(track)
      else:
        tags['track'] = int(tags['track'])
    except ValueError:
      try:
        # Converts A to 0, B to 1 etc
        tags['track'] = int(str(ord(track[0].upper()) - 65) + str(track[1:]))
      except ValueError:
        # strip track so backend does not crash if not parseable
        tags['track'] = ""
            
    self.info.update(tags)

    
    
