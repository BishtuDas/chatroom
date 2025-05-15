from django.urls import path, re_path
from chat import views

urlpatterns = [
    path('', views.join_room, name='join_room'),
    re_path(r'^chat/(?P<room_name>[\w-]+)/$', views.chat_room, name='chat_room'),
]