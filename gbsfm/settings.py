import sys, os
import gbsfm.other_settings as other_settings
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


sys.path.append(os.path.join(BASE_DIR, 'apps')) #to make forum work

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ADMINS = [] #not used?

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'gbsfm',
        'USER': other_settings.DATABASE_USERNAME,
        'PASSWORD': other_settings.DATABASE_PASSWORD,
        'HOST': other_settings.DATABASE_HOST,
        'ATOMIC_REQUESTS': True
    }
}

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '192.168.0.171', 'gbsfm', 'updated.gbs.fm', 'www.gbs.fm', 'gbs.fm', '192.168.0.134', 'gbsfm.hemma.lokal', 'docker4', 'beta.gbs.fm']

TIME_ZONE = 'Europe/London'

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/
LANGUAGE_CODE = 'en-uk'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

USE_TZ = True

# Make this unique, and don't share it with anybody. Must be in other_settings.py
SECRET_KEY = other_settings.SECRET_KEY

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = 'static/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'playlist.context.SQLLogContextProcessor',
                'playlist.context.listenersContextProcessor',
                'playlist.context.positionContextProcessor',
                'playlist.context.commentProcessor',
                "playlist.context.nowPlayingContextProcessor",
                "playlist.context.newEditsContextProcessor",
                "playlist.context.newReportsContextProcessor",
                "django.contrib.messages.context_processors.messages"
            ],
        },
    },
]

WSGI_APPLICATION = 'gbsfm.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

ATOMIC_REQUESTS = True

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTH_PROFILE_MODULE = 'playlist.userprofile'

ROOT_URLCONF = 'gbsfm.urls'

INSTALLED_APPS = [
    'playlist',
    'forum',
    'Plex',
    # 'markdown_deux',doesnt look like its used
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',  # delete?
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites'

]

FILE_UPLOAD_MAX_MEMORY_SIZE = 0

LOGIN_REDIRECT_URL = 'playlist'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SERIALIZATION_MODULES = { 'json': 'wadofstuff.django.serializers.json' }

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
#MAX_UPLOAD_SIZE = 115000000
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
#LOG_DIR = 'ftplog'
EMOTICONS_URL = "http://forums.somethingawful.com/misc.php?action=showsmilies"

#forums settings

COMMENTS_ALLOW_PROFANITIES = True

# cache setting

CACHE_BACKEND = os.path.join(BASE_DIR, 'cache')
CACHE_MIDDLEWARE_SECONDS = 1
