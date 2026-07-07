from django.db import models
from django.contrib.auth.models import User

class User_Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, default='avatars/default.png')
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'Profile for {self.user.username}'
    
class Chat(models.Model):
    user1 = models.ForeignKey(User, related_name='chats_as_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='chats_as_user2', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f'{self.user1} and {self.user2}'

class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message_text = models.TextField(blank=True, null=True)  # Allow empty messages for media-only messages
    attached_file = models.FileField(upload_to='chat_media/', blank=True, null=True)  # Renamed from 'media'
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender} to {self.chat}: {self.message_text[:20]}'

class Media(models.Model):
    IMAGE = 'image'
    VIDEO = 'video'
    AUDIO = 'audio'
    DOCUMENT = 'document'
    OTHER = 'other'

    MEDIA_TYPE_CHOICES = [
        (IMAGE, 'Image'),
        (VIDEO, 'Video'),
        (AUDIO, 'Audio'),
        (DOCUMENT, 'Document'),
        (OTHER, 'Other'),
    ]

    message = models.ForeignKey(
        Message,
        related_name='attached_media',  # Unique related_name to avoid conflict
        on_delete=models.CASCADE
    )
    media_type = models.CharField(max_length=50, choices=MEDIA_TYPE_CHOICES)
    media_url = models.URLField()

    def __str__(self):
        return f'Media for message {self.message.id}: {self.media_url}'
    AUDIO = 'audio'
    DOCUMENT = 'document'
    OTHER = 'other'

    MEDIA_TYPE_CHOICES = [
        (IMAGE, 'Image'),
        (VIDEO, 'Video'),
        (AUDIO, 'Audio'),
        (DOCUMENT, 'Document'),
        (OTHER, 'Other'),
    ]

    message = models.ForeignKey(Message, related_name='media', on_delete=models.CASCADE)
    media_type = models.CharField(max_length=50, choices=MEDIA_TYPE_CHOICES)
    media_url = models.URLField()

    def __str__(self):
        return f'Media for message {self.message.id}: {self.media_url}'

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, null=True, blank=True, on_delete=models.SET_NULL)
    notification_text = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notification for {self.user}: {self.notification_text[:20]}'

class Group(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='created_groups', on_delete=models.CASCADE)
    def __str__(self):
        return self.name

class GroupMembership(models.Model):
    group = models.ForeignKey(Group, related_name='memberships', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='group_memberships', on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')

    def __str__(self):
        return f'{self.user} in {self.group}'

class GroupMessage(models.Model):
    group = models.ForeignKey(Group, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender} in {self.group}: {self.message_text[:20]}'

class GroupMedia(models.Model):
    IMAGE = 'image'
    VIDEO = 'video'
    AUDIO = 'audio'
    DOCUMENT = 'document'
    OTHER = 'other'

    MEDIA_TYPE_CHOICES = [
        (IMAGE, 'Image'),
        (VIDEO, 'Video'),
        (AUDIO, 'Audio'),
        (DOCUMENT, 'Document'),
        (OTHER, 'Other'),
    ]
    message = models.ForeignKey(GroupMessage, related_name='media', on_delete=models.CASCADE)
    media_type = models.CharField(max_length=50, choices=MEDIA_TYPE_CHOICES)
    media_url = models.URLField()

    def __str__(self):
        return f'Media for group message {self.message.id}: {self.media_url}'
