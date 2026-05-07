from .models import Project, ProjectMember


def create_project(validated_data: dict, user) -> Project:
    project = Project.objects.create(owner=user, **validated_data)
    ProjectMember.objects.create(project=project, user=user, role='owner')
    return project


def sync_related_items(project: Project, user, data: dict) -> None:
    from apps.meetings.models import Meeting
    from apps.todos.models import Todo
    from apps.schedules.models import Schedule

    if 'meetingIds' in data:
        Meeting.objects.filter(project=project, created_by=user).update(project=None)
        ids = data.get('meetingIds') or []
        if ids:
            Meeting.objects.filter(created_by=user, id__in=ids).update(project=project)

    if 'todoIds' in data:
        Todo.objects.filter(project=project, user=user).update(project=None)
        ids = data.get('todoIds') or []
        if ids:
            Todo.objects.filter(user=user, id__in=ids).update(project=project)

    if 'scheduleIds' in data:
        Schedule.objects.filter(project=project, user=user).update(project=None)
        ids = data.get('scheduleIds') or []
        if ids:
            Schedule.objects.filter(user=user, id__in=ids).update(project=project)
