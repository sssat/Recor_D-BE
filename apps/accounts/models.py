from django.contrib.auth.models import AbstractUser
from django.db import models
from common.models import TimeStampedModel


class User(AbstractUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class SocialAccount(TimeStampedModel):
    PROVIDER_CHOICES = [
        ('kakao', 'Kakao'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_accounts')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    social_id = models.CharField(max_length=200)

    class Meta:
        unique_together = ('provider', 'social_id')

    def __str__(self):
        return f"{self.provider}:{self.user.email}"
