# -*- coding: utf-8 -*-
from playlist.models import *
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django import forms

class ArtistAdmin(admin.ModelAdmin):
  search_fields = ['name']

class UserProfileAdmin(admin.ModelAdmin):
  search_fields = ['user__username']

# Hide username so we don't get validation errors for ones with spaces
class NoUsernameUserAdmin(UserAdmin):
  fieldsets = (
        (None, {'fields': ('password',)}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

admin.site.unregister(User)
admin.site.register(User, NoUsernameUserAdmin)
admin.site.register(Artist, ArtistAdmin)
admin.site.register(Album)
admin.site.register(Song)
admin.site.register(PlaylistEntry)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Settings)
admin.site.register(SongDir)
admin.site.register(Emoticon)
