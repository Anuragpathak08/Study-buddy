from django.contrib import admin
from .models import *

admin.site.register(Chat)
admin.site.register(Message)
admin.site.register(Media)
admin.site.register(Notification)
admin.site.register(Group)
admin.site.register(GroupMembership)
admin.site.register(GroupMessage)
admin.site.register(User_Profile)
admin.site.register(GroupMedia)
