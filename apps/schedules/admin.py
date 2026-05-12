from django.contrib import admin

from .models import Schedule


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'project', 'type', 'color', 'start_datetime', 'end_datetime', 'is_all_day')
    list_filter = ('type', 'color', 'is_all_day')
