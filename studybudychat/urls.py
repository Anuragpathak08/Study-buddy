from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login_signup/', views.login_signup, name='login_signup'),
    path('chat/<int:chat_id>/', views.chat, name='chat'),
    path('chat/<int:chat_id>/send/', views.send_message, name='send_message'),
    path('chat_list/', views.chat_list, name='chat_list'),
    path('newchat/', views.new_chat, name='new_chat'),
    path('newchat/start/<int:user_id>/', views.start_chat, name='start_chat'),
    path('newgroup/', views.new_group, name='new_group'),
    path('newgroup/create/', views.create_group, name='create_group'),
    path('group/<int:group_id>/', views.group_chat, name='group_chat'),
    path('group/<int:group_id>/send/', views.send_group_message, name='send_group_message'),
    path('profile/', views.profile, name='profile'),  # Add this line
    path('logout/', views.logout_view, name='logout'),
]