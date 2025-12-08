from django.shortcuts import render
from .models import Chat

# Create your views here.
def chat_view(request):
    chats = Chat.objects.all().order_by('-created_at')
    context = {
        'chats': chats
    }
    return render(request, 'chat/chat.html', context)