from django.db import models

class ChatMessage(models.Model):
    user = models.CharField(max_length=100)  # Changed to CharField
    room = models.CharField(max_length=100)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)