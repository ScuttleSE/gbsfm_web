import re

from urllib.error import URLError
from urllib.request import Request
from urllib.request import urlopen

# import urllib2
import http.cookiejar as cookielib
import urllib.parse


from django.conf import settings

user_agent_header = {'User-Agent': "kalleboo v1.0"}
login_addr = "https://forums.somethingawful.com/account.php"
profile_addr = "https://forums.somethingawful.com/member.php?action=getinfo&username="

sa_username = settings.SA_USERNAME
sa_password = settings.SA_PASSWORD

userid = re.compile(r'<input type="hidden" name="userid" value="(\d+)">')


randcode = lambda: md5(str(getrandbits(64))).hexdigest()


class IDNotFoundError(Exception): pass

class SAProfile:

  def __init__(self, username):
    """Login and load the profile page. Error handling left to caller."""
    cj = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)

    login_args = urllib.parse.urlencode([("username", sa_username), ("password", sa_password), ("action", "login")])
    login_request = Request(login_addr, login_args, headers=user_agent_header)
    opener.open(login_request) #login

    profile_request = Request(profile_addr + urllib.parse.quote(username), headers=user_agent_header)
    self.page = opener.open(profile_request).read()
    #print(self.page)

  def get_id(self):
    s = userid.search(self.page)
    if s:
      return int(s.group(1))
    else:
      raise IDNotFoundError

  def has_authcode(self, code):
    return code in self.page

if __name__ == "__main__":
  p = SAProfile("Scuttle_SE")
  print(p.get_id())
  print(p.has_authcode("farts"))


