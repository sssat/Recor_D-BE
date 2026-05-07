from rest_framework import serializers
from django.db import transaction
from apps.accounts.serializers import UserSerializer
from .models import Project, ProjectMember
from .services import create_project, sync_related_items


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
        project = create_project(validated_data, user)
        sync_related_items(project, user, self.context['request'].data)
        return project

    @transaction.atomic
    def update(self, instance, validated_data):
        project = super().update(instance, validated_data)
        sync_related_items(project, self.context['request'].user, self.context['request'].data)
        return project
