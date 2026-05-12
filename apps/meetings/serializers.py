from rest_framework import serializers
from apps.projects.models import Project
from .models import Meeting


def normalize_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(',') if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raise serializers.ValidationError('Must be a list or comma-separated string.')


def normalize_checks(values, action_items):
    checks = values if isinstance(values, list) else []
    return [bool(checks[index]) if index < len(checks) else False for index, _ in enumerate(action_items)]


class MeetingSerializer(serializers.ModelSerializer):
    project = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    projectId = serializers.IntegerField(source='project_id', read_only=True)
    participants = serializers.ListField(
        child=serializers.CharField(allow_blank=False),
        required=False,
    )
    tags = serializers.ListField(
        child=serializers.CharField(allow_blank=False),
        required=False,
    )
    durationMinutes = serializers.IntegerField(write_only=True, required=False, min_value=0)
    keyPoints = serializers.ListField(
        child=serializers.CharField(allow_blank=False),
        source='key_points',
        required=False,
    )
    actionItems = serializers.ListField(
        child=serializers.CharField(allow_blank=False),
        source='action_items',
        required=False,
    )
    actionItemChecks = serializers.ListField(
        child=serializers.BooleanField(),
        source='action_item_checks',
        required=False,
    )
    sourceType = serializers.ChoiceField(
        source='source_type',
        choices=['manual', 'upload'],
        required=False,
    )
    audioFileName = serializers.CharField(
        source='audio_file_name',
        required=False,
        allow_blank=True,
    )
    aiSummary = serializers.CharField(source='ai_summary', read_only=True)
    isSummarized = serializers.BooleanField(source='is_summarized', read_only=True)
    summarizedAt = serializers.DateTimeField(source='summarized_at', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    ai_summary = serializers.CharField(read_only=True)
    key_points = serializers.ListField(child=serializers.CharField(), read_only=True)
    action_items = serializers.ListField(child=serializers.CharField(), read_only=True)
    action_item_checks = serializers.ListField(child=serializers.BooleanField(), read_only=True)
    is_summarized = serializers.BooleanField(read_only=True)
    summarized_at = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Meeting
        fields = (
            'id', 'project', 'projectId', 'title', 'date', 'duration',
            'durationMinutes', 'participants', 'summary', 'tags', 'transcript',
            'aiSummary', 'keyPoints', 'actionItems', 'actionItemChecks',
            'sourceType', 'audioFileName', 'isSummarized', 'summarizedAt',
            'createdAt', 'updatedAt',
            'ai_summary', 'key_points', 'action_items', 'action_item_checks',
            'is_summarized', 'summarized_at', 'created_at', 'updated_at',
        )
        read_only_fields = (
            'id', 'projectId', 'aiSummary', 'isSummarized', 'summarizedAt',
            'createdAt', 'updatedAt', 'ai_summary', 'key_points',
            'action_items', 'action_item_checks', 'is_summarized',
            'summarized_at', 'created_at', 'updated_at',
        )

    def to_internal_value(self, data):
        mutable_data = data.copy()
        for field_name in ('participants', 'tags', 'keyPoints', 'actionItems'):
            value = mutable_data.get(field_name)
            if isinstance(value, str):
                mutable_data.setlist(field_name, normalize_list(value)) if hasattr(mutable_data, 'setlist') else mutable_data.__setitem__(field_name, normalize_list(value))
        return super().to_internal_value(mutable_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['project'] = instance.project.name if instance.project else ''
        data['durationMinutes'] = self._duration_to_minutes(instance.duration)
        return data

    def validate_participants(self, value):
        return normalize_list(value)

    def validate_tags(self, value):
        return normalize_list(value)

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        project_value = attrs.pop('project', serializers.empty)
        duration_minutes = attrs.pop('durationMinutes', None)

        if project_value is not serializers.empty:
            attrs['project'] = self._resolve_project(project_value, user)

        if duration_minutes is not None:
            attrs['duration'] = f'{duration_minutes}분'

        action_items = attrs.get('action_items')
        if action_items is not None:
            attrs['action_items'] = normalize_list(action_items)
            attrs['action_item_checks'] = normalize_checks(
                attrs.get('action_item_checks', []),
                attrs['action_items'],
            )
        elif 'action_item_checks' in attrs:
            current_items = getattr(self.instance, 'action_items', [])
            attrs['action_item_checks'] = normalize_checks(attrs['action_item_checks'], current_items)

        if 'key_points' in attrs:
            attrs['key_points'] = normalize_list(attrs['key_points'])

        return attrs

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def _resolve_project(self, value, user):
        if value in (None, ''):
            return None

        qs = Project.objects.filter(user=user)
        if isinstance(value, int) or str(value).isdigit():
            return qs.filter(pk=value).first()
        return qs.filter(name=str(value).strip()).first()

    def _duration_to_minutes(self, value):
        digits = ''.join(char for char in str(value or '') if char.isdigit())
        return int(digits) if digits else 0


class MeetingDraftUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    project = serializers.CharField(required=False, allow_blank=True)
