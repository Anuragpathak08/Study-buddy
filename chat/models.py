from django.db import models
from django.conf import settings

# Create your models here.
class Conversation(models.Model):
    name = models.TextField(max_length=255, blank=True, null=True)
    isgroup = models.models.BooleanField(default = True)
    participant = models.ManyToManyField( settings.AUTH_MODEL_USER)

class Chat(models.Model):
    conv = models.ForeignKey(Conversation , on_delete=Cas)