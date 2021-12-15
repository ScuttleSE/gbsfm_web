# -*- coding: utf-8 -*-
import os.path

from django.contrib.auth import views as auth_views
from django.conf.urls import url, include
from django.conf import settings
from django.views.static import serve
from django.contrib import admin
admin.autodiscover()

import playlist.views


defaultdict = { 'groupName': 'example' }

urlpatterns = [

url(r'^forum/', include('forum.urls')),
url(r'^admin/', admin.site.urls),
url(r'^$', playlist.views.playlist),
url(r'^playlist(/(?P<lastid>\d+))?$', playlist.views.playlist, {}, name="playlist"),
url(r'^splaylist$', playlist.views.splaylist),
url(r'^images/(?P<path>.*)$', serve, {'document_root': settings.IMAGES_DIR}),
url(r'^static/(?P<path>.*)$', serve, {'document_root': '/srv/pydj/static'}),
url(r'^emoticons/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.IMAGES_DIR, "emoticons")}, name="emoticons"),
url(r'^upload/?$', playlist.views.upload, name='upload'),
url(r'^stats/?$', playlist.views.globalstats, name='globalstats'),
url(r'^search/?$', playlist.views.search, name='search'),
url(r'^comment/(\d+)$', playlist.views.comment, name='comment'),
url(r'^comment/(?P<commentid>\d+)/delete$', playlist.views.delete_comment, {}, name="delete_comment"),
url(r'^artist/(?P<artistid>\d+)$', playlist.views.artist, {}, name="artist"),
url(r'^user/(?P<userid>\d+)$', playlist.views.user, {}, name="user"),
url(r'^user/(?P<userid>\d+)/givetoken$', playlist.views.give_token, {}, name="give_token"),
url(r'^.*/images/(?P<path>.*)$', serve, {'document_root': settings.IMAGES_DIR}),
url(r'^.*/emoticons/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.IMAGES_DIR, "emoticons")}, name="emoticons"),
url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
url(r'^.*login/?$', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
url(r'^logout/?$', auth_views.logout_then_login, name='logout'),
url(r'^add/(?P<songid>\d+)$', playlist.views.add, name='add'),
url(r'^next/(?P<authid>.+)$', playlist.views.next, name='next'),
url(r'^register/?$', playlist.views.newregister, name='register'),
url(r'^song/(?P<songid>\d+)(?P<edit>/edit)?$', playlist.views.song, {}, name="song"),
url(r'^song/(?P<songid>\d+)/rate/(?P<vote>\d+)/$', playlist.views.rate, name="rate"),
url(r'^song/(?P<songid>\d+)/ban$', playlist.views.bansong, name="bansong"),
url(r'^song/(?P<songid>\d+)/download$', playlist.views.download_song, name='download_song'),
url(r'^song/(?P<songid>\d+)/delete$', playlist.views.deletesong, name='deletesong'),
url(r'^song/(?P<songid>\d+)/delete/(?P<confirm>.+)$', playlist.views.deletesong, name='deletesongconfirm'),
url(r'^song/(?P<songid>\d+)/report$', playlist.views.song_report, name='song_report'),
url(r'^song/(\d+)/unban/?(\d+)$', playlist.views.unbansong, name='unbansong'),
url(r'^song/(\d+)/merge/(\d+)$', playlist.views.merge_song, name="marge"),
url(r'^playlist/remove/(\d+)$', playlist.views.removeentry, name='removeentry'),
url(r'^reports$', playlist.views.reports, {}, name="reports"),
url(r'^reports/approve/(?P<approve>\d+)', playlist.views.reports, name="reportsapprove"),
url(r'^reports/deny/(?P<deny>\d+)', playlist.views.reports, name="reportsdeny"),
url(r'^editqueue/?$', playlist.views.edit_queue, {}, name="edit_queue"),
url(r'^editqueue/approve/(?P<approve>\d+)', playlist.views.edit_queue, name="edit_queue_approve"),
url(r'^editqueue/deny/(?P<deny>\d+)', playlist.views.edit_queue, name="edit_queue_deny"),
url(r'^album/(\d+)$', playlist.views.album, {}, name="album"),
url(r'^skip$', playlist.views.skip, name="skip"),
url(r'^artists/(123|all|\w)/(\d+)$', playlist.views.listartists, name='listartists'),
url(r'^api/(?P<resource>.+)$', playlist.views.api, name='api'),
url(r'^ajax$', playlist.views.ajax, name='ajax'),
url(r'^favourite/(?P<songid>\d+)$', playlist.views.favourite, name='favourite'),
url(r'^unfavourite/(?P<songid>\d+)$', playlist.views.unfavourite, name='unfavourite'),
url(r'^settings/?$', playlist.views.user_settings, {}, name="user_settings"),
url(r'^keygen/?$', playlist.views.keygen, {}, name="keygen"),
url(r'^g2admin$', playlist.views.g2admin, {}, name="g2admin"),
url(r'^g2streampw$', playlist.views.g2streampw, {}, name="g2streampw"),
url(r'^stop_stream$', playlist.views.stop_stream, {}, name="stop_stream"),
url(r'^start_metadataupdater$', playlist.views.start_metadataupdater, {}, name="start_metadataupdater"),
url(r'^stop_metadataupdater$', playlist.views.stop_metadataupdater, {}, name="stop_metadataupdater"),
url(r'^restart_stream$', playlist.views.restart_stream, {}, name="restart_stream"),
url(r'^stop_stream2$', playlist.views.stop_stream2, {}, name="stop_stream2"),
url(r'^start_stream2$', playlist.views.start_stream2, {}, name="start_stream2"),
url(r'^stop_stream3$', playlist.views.stop_stream3, {}, name="stop_stream3"),
url(r'^start_stream3$', playlist.views.start_stream3, {}, name="start_stream3"),
url(r'^restart_socks$', playlist.views.restart_socks, {}, name="restart_socks"),
url(r'^restart_shoes$', playlist.views.restart_shoes, {}, name="restart_shoes"),
url(r'^restart_linkbot$', playlist.views.restart_linkbot, {}, name="restart_linkbot"),
url(r'^restart_ftp$', playlist.views.restart_ftp, {}, name="restart_ftp"),
url(r'^start_ftp$', playlist.views.start_ftp, {}, name="start_ftp"),
url(r'^stop_ftp$', playlist.views.stop_ftp, {}, name="stop_ftp"),
url(r'^start_listeners$', playlist.views.start_listeners, {}, name="start_listeners"),
url(r'^start_remaining$', playlist.views.start_remaining, {}, name="start_remaining"),
url(r'^carplay$', playlist.views.carplay, {}, name="carplay"),
#javascript stuff
url(r'^artist/$', playlist.views.artist, {}, name="artist_js"),
url(r'^song/$', playlist.views.song, {}, name="song_js"),
url(r'^user/$', playlist.views.user, {}, name="user_js"),
url(r'^playlist/remove/$', playlist.views.removeentry, {}, name="removeentry_js"),
]
