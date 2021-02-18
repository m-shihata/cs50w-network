from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    followers = models.ManyToManyField("self", blank=True, related_name="following", symmetrical=False)

    def serialize(self):
        return {
            "username": self.username,
            "joined" : self.date_joined.strftime("%b %Y"),
            "followers": self.followers.count(),
            "following": self.following.count(),
        }


class Post(models.Model):
    publisher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.CharField(max_length=280)
    timestamp = models.DateTimeField(auto_now_add=True)

    def serialize(self, user):

        return {
            "id": self.id,
            "publisher": self.publisher.username,
            "content": self.content,
            "likes": self.likes.count(),
            "liked": user.is_authenticated and self.likes.filter(liked_by=user).count() == 1,
            "timestamp": self.timestamp.strftime("%-I:%M %p - %b %-d %Y")
        }


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    liked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    timestamp = models.DateTimeField(auto_now_add=True)
