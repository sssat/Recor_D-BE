from django.db import models
from django.conf import settings
from common.models import TimeStampedModel


class Project(TimeStampedModel):
    STATUS_CHOICES = [
        ('inProgress', '진행중'),
        ('completed', '완료'),
        ('planning', '준비중'),
    ]
    COLOR_CHOICES = [
        ('green', 'green'),
        ('blue', 'blue'),
        ('teal', 'teal'),
        ('yellow', 'yellow'),
        ('brightGreen', 'brightGreen'),
        ('red', 'red'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects'
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='inProgress')
    tags = models.JSONField(default=list)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='green')

    def __str__(self):
        return self.name


class ProjectMember(TimeStampedModel):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_memberships'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')

    class Meta:
        unique_together = ('project', 'user')

    def __str__(self):
        return f"{self.project.name} - {self.user.email} ({self.role})"
