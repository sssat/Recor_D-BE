from rest_framework import serializers
from django.db import transaction
from apps.accounts.serializers import UserSerializer
from .models import Project, ProjectMember


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ProjectMember
        fields = ('id', 'user', 'user_id', 'role', 'created_at')
        read_only_fields = ('id', 'created_at')


class ProjectSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    startDate = serializers.DateField(source='start_date', allow_null=True, required=False)
    endDate = serializers.DateField(source='end_date', allow_null=True, required=False)
    colorKey = serializers.ChoiceField(source='color', choices=[c[0] for c in Project.COLOR_CHOICES])
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    meetingCount = serializers.SerializerMethodField()
    todoCount = serializers.SerializerMethodField()
    completedTodoCount = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    meetingIds = serializers.SerializerMethodField()
    todoIds = serializers.SerializerMethodField()
    scheduleIds = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            'id', 'name', 'description', 'owner',
            'startDate', 'endDate', 'status', 'tags', 'colorKey',
            'meetingCount', 'todoCount', 'completedTodoCount', 'progress',
            'meetingIds', 'todoIds', 'scheduleIds',
            'createdAt',
        )
        read_only_fields = ('id', 'owner', 'createdAt')

    def get_meetingCount(self, obj):
        return len(obj.meetings.all())

    def get_todoCount(self, obj):
        return len(obj.todos.all())

    def get_completedTodoCount(self, obj):
        return sum(1 for t in obj.todos.all() if t.status == 'done')

    def get_progress(self, obj):
        todos = obj.todos.all()
        total = len(todos)
        if total == 0:
            return 0
        return round(sum(1 for t in todos if t.status == 'done') / total * 100)

    def get_meetingIds(self, obj):
        return [m.id for m in obj.meetings.all()]

    def get_todoIds(self, obj):
        return [t.id for t in obj.todos.all()]

    def get_scheduleIds(self, obj):
        return [s.id for s in obj.schedules.all()]

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        project = Project.objects.create(owner=user, **validated_data)
        ProjectMember.objects.create(project=project, user=user, role='owner')
        self._sync_related(project)
        return project

    @transaction.atomic
    def update(self, instance, validated_data):
        project = super().update(instance, validated_data)
        self._sync_related(project)
        return project

    def _sync_related(self, project):
        from apps.meetings.models import Meeting
        from apps.todos.models import Todo
        from apps.schedules.models import Schedule

        user = self.context['request'].user
        data = self.context['request'].data

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
