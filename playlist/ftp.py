# -*- coding: utf-8 -*-
import sys
sys.path.append('/srv')
sys.path.append('/srv/pydj')
sys.path.append('/srv/pydj/apps')
print(sys.path)
import os
import os.path
import threading
import time
import errno
import logging
import django

from django.conf import settings

#settings.configure()
#django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.management.base import BaseCommand

from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.authorizers import DummyAuthorizer, AuthorizerError

from playlist.upload import UploadedFile, UnsupportedFormatError, CorruptFileError
from playlist.models import FileTooBigError, DuplicateError


class Command(BaseCommand):

    help = "Run the ftp server (this command will run forever)"

    def handle(self, **options):
        main()

BASE_DIR = settings.FTP_BASE_DIR

class G2FTPHandler(FTPHandler):
  
  def __init__(self, conn, server, ioloop):
    FTPHandler.__init__(self, conn, server, ioloop)
    
  def on_file_received(self, file):
  
    def handle():
      try:
        User.objects.get(username=self.username).userprofile.uploadSong(UploadedFile(file))
      except UnsupportedFormatError, e:
        self.respond("557 ERROR: file format not supported")
        return
      except CorruptFileError, e:
        self.respond("554 ERROR: file corrupt")
        return
      except FileTooBigError, e:
        self.respond("555 ERROR: file too big. Hi Jormagund!")
        return
      except DuplicateError:
        self.respond("556 ERROR: file an exact duplicate. Search before uploading!")
        return
      finally:
        os.remove(file)
      self.sleeping = False
      
    self.sleeping = True
    threading.Thread(target=handle).start()

class G2Authorizer(DummyAuthorizer):

  def _create_dir_if_neccessary(self, path):
    try:
      os.makedirs(path)
    except OSError as e:
      if e.errno != errno.EEXIST:
        raise

  def validate_authentication(self, username, password, handler):
    User.objects.update() #avoid THE FTP BUG!
    if not bool(authenticate(username=username, password=password)):
      return False
    homedir = os.path.join(BASE_DIR, username.lower())
    self._create_dir_if_neccessary(homedir)      
    try:
      self.add_user(username, 'password', homedir, perm='lweadf') #list, write, CWD
    except ValueError:
      pass #already logged in
      
    return True
  
now = lambda: time.strftime("[%Y-%b-%d %H:%M:%S]")
   
def standard_logger(msg):
    f1.write("%s %s\n" %(now(), msg))
    f1.flush()
   
def line_logger(msg):
    f2.write("%s %s\n" %(now(), msg))
    f2.flush()
    
def error_logger(msg):
    f3.write("%s %s\n" %(now(), msg))
    f3.flush()
  
def main():
  logging.basicConfig(filename='/srv/logs/ftpd.log', level=logging.INFO)
  authorizer = G2Authorizer()
  ftp_handler = G2FTPHandler
  ftp_handler.authorizer = authorizer
  ftp_handler.masquerade_address = '85.24.128.115'
  ftp_handler.passive_ports = range(2102,2150)

  address = ('', 2100)
  ftpd = FTPServer(address, ftp_handler)
  ftpd.serve_forever()

