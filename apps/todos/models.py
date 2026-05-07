from django.db import models
from django.conf import settings
from common.models import TimeStampedModel


class Todo(TimeStampedModel):
    PRIORITY_CHOICES = [('low', '낮음'), ('medium', '보통'), ('high', '높음')]
    STATUS_CHOICES = [('todo', '할 일'), ('in_progress', '진행 중'), ('done', '완료')]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='todos'
    )
    project = models.ForeignKey(
        'projects.Project', on_delete=models.SET_NULL,
        related_name='todos', null=True, blank=True,
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    due_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title
