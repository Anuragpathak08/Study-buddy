from django.db import models

# Create your models here.
class Chat(models.Model):
    user1  = models.ForeignKey("app.Model", verbose_name=_(""), on_delete=models.CASCADE)
    user2 = models.ForeignKey("app.Model", verbose_name=_(""), on_delete=models.CASCADE)