from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Schedule(TimeStampedModel):
    TYPE_CHOICES = [
        ('meeting', '회의'),
        ('deadline', '마감일'),
        ('presentation', '발표'),
        ('other', '기타'),
    ]
    COLOR_CHOICES = [
        ('green', 'green'),
        ('blue', 'blue'),
        ('teal', 'teal'),
        ('yellow', 'yellow'),
        ('brightGreen', 'brightGreen'),
        ('red', 'red'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='schedules'
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        related_name='schedules',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='other')
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='green')
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_all_day = models.BooleanField(default=False)
    location = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return self.title
