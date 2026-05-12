from django.contrib import admin
from .models import Project, ProjectMember


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'status', 'color', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'color')
    inlines = [ProjectMemberInline]
