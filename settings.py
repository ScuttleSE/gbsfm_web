# -*- coding: utf-8 -*-
# Django settings for pydj project.
import sys, os

# other_settings.py should have an SA username and password and a secret key
import other_settings

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
# Assumes that setings.py is in the base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.join(BASE_DIR, 'apps')) #to make forum work

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ADMINS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'gbsfm',
        'USER': other_settings.DATABASE_USERNAME,
        'PASSWORD': other_settings.DATABASE_PASSWORD,
	'HOST': other_settings.DATABASE_HOST
    }
}

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '192.168.0.171', 'gbsfm', 'updated.gbs.fm', 'www.gbs.fm', 'gbs.fm', '192.168.0.134', 'gbsfm.hemma.lokal']

TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-uk'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody. Must be in other_settings.py
SECRET_KEY = other_settings.SECRET_KEY

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = "/static/"

# List of callables that know how to import templates from various sources.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['/srv/pydj/playlist/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.request",
                'playlist.context.SQLLogContextProcessor',
                'playlist.context.listenersContextProcessor',
                'playlist.context.positionContextProcessor',
                'playlist.context.commentProcessor',
                "playlist.context.nowPlayingContextProcessor",
                "playlist.context.newEditsContextProcessor",
                "playlist.context.newReportsContextProcessor",
                "django.contrib.messages.context_processors.messages"
            ]
        },
    },
]

ATOMIC_REQUESTS = True

MIDDLEWARE = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware'
)


AUTH_PROFILE_MODULE = 'playlist.userprofile'

ROOT_URLCONF = 'urls'

INSTALLED_APPS = (
    'playlist',
    'forum',
    'markdown_deux',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin'
)


PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher'
]


LOGIN_REDIRECT_URL = 'playlist'
LOGIN_URL = 'login'

FILE_UPLOAD_MAX_MEMORY_SIZE = 0

ACCOUNT_ACTIVATION_DAYS= 2

SERIALIZATION_MODULES = { 'json' : 'wadofstuff.django.serializers.json' }

# GBSFM settings

# IMPORTANT - SA validation will not happen if this is set to False
IS_LIVE = True

LOGIC_DIR = os.path.join(BASE_DIR, 'playlist', 'logic')
ICES_CONF = os.path.join(LOGIC_DIR, 'ices.conf')
IMAGES_DIR = os.path.join(BASE_DIR, 'playlist', 'images')

SCTRANS_DIR = '/srv/sc_trans'
SCTRANS_CONF = os.path.join(SCTRANS_DIR, 'sc_trans.conf')
SCSERV_DIR = os.path.join(BASE_DIR, 'sc_serv')
SCSERV_CONF = os.path.join(SCSERV_DIR, 'sc_serv.conf')

# The password for the /next endpoint
NEXT_PASSWORD = other_settings.NEXT_PASSWORD

#FTP_BASE_DIR = os.path.join(BASE_DIR, 'ftpdir')
FTP_BASE_DIR = '/srv/ftpdir'
MAX_UPLOAD_SIZE = 115000000
MAX_UPLOAD_SIZE = 536870912
MAX_SONG_LENGTH = 660

# Add SA account details to other_settings.py before going live
SA_USERNAME = other_settings.SA_USERNAME
SA_PASSWORD = other_settings.SA_PASSWORD

# Max number of songs allowed to be queued by a user without tokens
PLAYLIST_MAX = 1

# How long before a song can be played again, in hours
REPLAY_INTERVAL = 24 * 8

#STREAMINFO_URL = "http://gbsfm:8000/statistics"
STREAMINFO_URL = "http://admin:adminpassword@192.168.0.154:8888/admin/stats"
LOG_LEVEL = "DEBUG"
LOG_FILE = os.path.join(BASE_DIR, 'pydj.log')
SHOW_QUERIES = False
LOG_DIR = '/srv/logs'
EMOTICONS_URL = "http://forums.somethingawful.com/misc.php?action=showsmilies"

#forums settings

COMMENTS_ALLOW_PROFANITIES = True

# cache setting

CACHE_BACKEND = os.path.join(BASE_DIR, 'cache')
CACHE_MIDDLEWARE_SECONDS = 1

# Cookie timeout settings
# SESSION_COOKIE_AGE = 1209600
SESSION_COOKIE_AGE =  7889400