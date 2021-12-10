"""olitest URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  re_path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  re_path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  re_path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.views.static import serve
import playlist.views
import os


defaultdict = { 'groupName': 'example' }

urlpatterns = [

re_path(r'^forum/', include('forum.urls')),
re_path(r'^admin/', admin.site.urls),
re_path(r'^$', playlist.views.playlist),
re_path(r'^playlist(/(?P<lastid>\d+))?$', playlist.views.playlist, {}, name="playlist"),
re_path(r'^splaylist$', playlist.views.splaylist),
re_path(r'^images/(?P<path>.*)$', serve, {'document_root': settings.IMAGES_DIR}),
re_path(r'^static/(?P<path>.*)$', serve, {'document_root': '/srv/pydj/static'}),
re_path(r'^emoticons/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.IMAGES_DIR, "emoticons")}, name="emoticons"),
re_path(r'^upload/?$', playlist.views.upload, name='upload'),
re_path(r'^stats/?$', playlist.views.globalstats, name='globalstats'),
re_path(r'^search/?$', playlist.views.search, name='search'),
re_path(r'^comment/(\d+)$', playlist.views.comment, name='comment'),
re_path(r'^comment/(?P<commentid>\d+)/delete$', playlist.views.delete_comment, {}, name="delete_comment"),
re_path(r'^artist/(?P<artistid>\d+)$', playlist.views.artist, {}, name="artist"),
re_path(r'^user/(?P<userid>\d+)$', playlist.views.user, {}, name="user"),
re_path(r'^user/(?P<userid>\d+)/givetoken$', playlist.views.give_token, {}, name="give_token"),
re_path(r'^.*/images/(?P<path>.*)$', serve, {'document_root': settings.IMAGES_DIR}),
re_path(r'^.*/emoticons/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.IMAGES_DIR, "emoticons")}, name="emoticons"),
re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
re_path(r'^.*login/?$', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
re_path(r'^logout/?$', auth_views.logout_then_login, name='logout'),
re_path(r'^add/(?P<songid>\d+)$', playlist.views.add, name='add'),
re_path(r'^next/(?P<authid>.+)$', playlist.views.next, name='next'),
re_path(r'^register/?$', playlist.views.newregister, name='register'),
re_path(r'^song/(?P<songid>\d+)(?P<edit>/edit)?$', playlist.views.song, {}, name="song"),
re_path(r'^song/(?P<songid>\d+)/rate/(?P<vote>\d+)/$', playlist.views.rate, name="rate"),
re_path(r'^song/(?P<songid>\d+)/ban$', playlist.views.bansong, name="bansong"),
re_path(r'^song/(?P<songid>\d+)/download$', playlist.views.download_song, name='download_song'),
re_path(r'^song/(?P<songid>\d+)/delete$', playlist.views.deletesong, name='deletesong'),
re_path(r'^song/(?P<songid>\d+)/delete/(?P<confirm>.+)$', playlist.views.deletesong, name='deletesongconfirm'),
re_path(r'^song/(?P<songid>\d+)/report$', playlist.views.song_report, name='song_report'),
re_path(r'^song/(\d+)/unban/?(\d+)$', playlist.views.unbansong, name='unbansong'),
re_path(r'^song/(\d+)/merge/(\d+)$', playlist.views.merge_song, name="marge"),
re_path(r'^playlist/remove/(\d+)$', playlist.views.removeentry, name='removeentry'),
re_path(r'^reports$', playlist.views.reports, {}, name="reports"),
re_path(r'^reports/approve/(?P<approve>\d+)', playlist.views.reports, name="reportsapprove"),
re_path(r'^reports/deny/(?P<deny>\d+)', playlist.views.reports, name="reportsdeny"),
re_path(r'^editqueue/?$', playlist.views.edit_queue, {}, name="edit_queue"),
re_path(r'^editqueue/approve/(?P<approve>\d+)', playlist.views.edit_queue, name="edit_queue_approve"),
re_path(r'^editqueue/deny/(?P<deny>\d+)', playlist.views.edit_queue, name="edit_queue_deny"),
re_path(r'^album/(\d+)$', playlist.views.album, {}, name="album"),
re_path(r'^skip$', playlist.views.skip, name="skip"),
re_path(r'^artists/(123|all|\w)/(\d+)$', playlist.views.listartists, name='listartists'),
re_path(r'^api/(?P<resource>.+)$', playlist.views.api, name='api'),
re_path(r'^ajax$', playlist.views.ajax, name='ajax'),
re_path(r'^favourite/(?P<songid>\d+)$', playlist.views.favourite, name='favourite'),
re_path(r'^unfavourite/(?P<songid>\d+)$', playlist.views.unfavourite, name='unfavourite'),
re_path(r'^settings/?$', playlist.views.user_settings, {}, name="user_settings"),
re_path(r'^keygen/?$', playlist.views.keygen, {}, name="keygen"),
re_path(r'^g2admin$', playlist.views.g2admin, {}, name="g2admin"),
re_path(r'^g2streampw$', playlist.views.g2streampw, {}, name="g2streampw"),
re_path(r'^stop_stream$', playlist.views.stop_stream, {}, name="stop_stream"),
re_path(r'^start_metadataupdater$', playlist.views.start_metadataupdater, {}, name="start_metadataupdater"),
re_path(r'^stop_metadataupdater$', playlist.views.stop_metadataupdater, {}, name="stop_metadataupdater"),
re_path(r'^restart_stream$', playlist.views.restart_stream, {}, name="restart_stream"),
re_path(r'^stop_stream2$', playlist.views.stop_stream2, {}, name="stop_stream2"),
re_path(r'^start_stream2$', playlist.views.start_stream2, {}, name="start_stream2"),
re_path(r'^stop_stream3$', playlist.views.stop_stream3, {}, name="stop_stream3"),
re_path(r'^start_stream3$', playlist.views.start_stream3, {}, name="start_stream3"),
re_path(r'^restart_socks$', playlist.views.restart_socks, {}, name="restart_socks"),
re_path(r'^restart_shoes$', playlist.views.restart_shoes, {}, name="restart_shoes"),
re_path(r'^restart_linkbot$', playlist.views.restart_linkbot, {}, name="restart_linkbot"),
re_path(r'^restart_ftp$', playlist.views.start_ftp, {}, name="restart_ftp"),
re_path(r'^start_ftp$', playlist.views.start_ftp, {}, name="start_ftp"),
re_path(r'^stop_ftp$', playlist.views.stop_ftp, {}, name="stop_ftp"),
re_path(r'^start_listeners$', playlist.views.start_listeners, {}, name="start_listeners"),
re_path(r'^start_remaining$', playlist.views.start_remaining, {}, name="start_remaining"),
re_path(r'^carplay$', playlist.views.carplay, {}, name="carplay"),
#javascript stuff
re_path(r'^artist/$', playlist.views.artist, {}, name="artist_js"),
re_path(r'^song/$', playlist.views.song, {}, name="song_js"),
re_path(r'^user/$', playlist.views.user, {}, name="user_js"),
re_path(r'^playlist/remove/$', playlist.views.removeentry, {}, name="removeentry_js"),
]
