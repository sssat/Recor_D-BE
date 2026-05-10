from rest_framework import serializers

from apps.projects.models import Project
from .models import Portfolio, StarEntry


def _split_action_text(value):
    if not value:
        return []
    return [line.strip() for line in value.splitlines() if line.strip()]


def _join_action_items(value):
    if isinstance(value, list):
        return '\n'.join(str(item).strip() for item in value if str(item).strip())
    return str(value or '').strip()


class StarEntrySerializer(serializers.ModelSerializer):
    action = serializers.JSONField(required=False)
    aiSummary = serializers.CharField(source='ai_summary', read_only=True)
    isSummarized = serializers.BooleanField(source='is_summarized', read_only=True)
    summarizedAt = serializers.DateTimeField(source='summarized_at', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = StarEntry
        fields = (
            'id', 'situation', 'task', 'action', 'result',
            'ai_summary', 'aiSummary', 'is_summarized', 'isSummarized',
            'summarized_at', 'summarizedAt', 'created_at', 'createdAt',
        )
        read_only_fields = (
            'id', 'ai_summary', 'aiSummary', 'is_summarized', 'isSummarized',
            'summarized_at', 'summarizedAt', 'created_at', 'createdAt',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['action'] = _split_action_text(instance.action)
        return data

    def to_internal_value(self, data):
        data = data.copy()
        if 'action' in data:
            data['action'] = _join_action_items(data.get('action'))
        return super().to_internal_value(data)


class PortfolioSerializer(serializers.ModelSerializer):
    projectId = serializers.IntegerField(source='project_id', allow_null=True, required=False)
    project = serializers.CharField(source='project.name', read_only=True)
    summary = serializers.CharField(source='description', allow_blank=True, required=False)
    keywords = serializers.ListField(
        source='tech_stack',
        child=serializers.CharField(),
        required=False,
    )
    githubUrl = serializers.URLField(source='github_url', allow_blank=True, required=False)
    deployUrl = serializers.URLField(source='deploy_url', allow_blank=True, required=False)
    thumbnailUrl = serializers.URLField(source='thumbnail_url', allow_blank=True, required=False)
    isPublic = serializers.BooleanField(source='is_public', required=False)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    situation = serializers.CharField(allow_blank=True, required=False)
    task = serializers.CharField(allow_blank=True, required=False)
    action = serializers.ListField(child=serializers.CharField(), required=False)
    result = serializers.CharField(allow_blank=True, required=False)
    aiSummary = serializers.SerializerMethodField()
    isSummarized = serializers.SerializerMethodField()
    summarizedAt = serializers.SerializerMethodField()
    star_entries = StarEntrySerializer(many=True, read_only=True)

    class Meta:
        model = Portfolio
        fields = (
            'id', 'project', 'projectId', 'title', 'description', 'summary',
            'tech_stack', 'keywords', 'github_url', 'githubUrl',
            'deploy_url', 'deployUrl', 'thumbnail_url', 'thumbnailUrl',
            'is_public', 'isPublic', 'situation', 'task', 'action', 'result',
            'aiSummary', 'isSummarized', 'summarizedAt',
            'star_entries', 'created_at', 'createdAt', 'updated_at', 'updatedAt',
        )
        read_only_fields = (
            'id', 'project', 'star_entries', 'created_at', 'createdAt',
            'updated_at', 'updatedAt', 'aiSummary', 'isSummarized', 'summarizedAt',
        )

    def _get_primary_star_entry(self, obj):
        entries = list(getattr(obj, 'star_entries').all())
        return entries[0] if entries else None

    def get_aiSummary(self, obj):
        entry = self._get_primary_star_entry(obj)
        return entry.ai_summary if entry else ''

    def get_isSummarized(self, obj):
        entry = self._get_primary_star_entry(obj)
        return entry.is_summarized if entry else False

    def get_summarizedAt(self, obj):
        entry = self._get_primary_star_entry(obj)
        return entry.summarized_at if entry and entry.summarized_at else None

    def to_internal_value(self, data):
        data = data.copy()
        if isinstance(data.get('keywords'), str):
            data['keywords'] = [
                item.strip() for item in data['keywords'].split(',') if item.strip()
            ]
        if 'action' in data:
            data['action'] = (
                data['action']
                if isinstance(data['action'], list)
                else [line.strip() for line in str(data['action']).splitlines() if line.strip()]
            )
        return super().to_internal_value(data)

    def validate(self, attrs):
        project_id = attrs.get('project_id')
        if project_id is None:
            return attrs
        user = self.context['request'].user
        if not Project.objects.filter(id=project_id, owner=user).exists():
            raise serializers.ValidationError({'projectId': '접근할 수 없는 프로젝트입니다.'})
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        entry = self._get_primary_star_entry(instance)
        data['situation'] = entry.situation if entry else ''
        data['task'] = entry.task if entry else ''
        data['action'] = _split_action_text(entry.action) if entry else []
        data['result'] = entry.result if entry else ''
        return data

    def _pop_star_data(self, validated_data):
        star_fields = {}
        for field in ('situation', 'task', 'action', 'result'):
            if field in validated_data:
                star_fields[field] = validated_data.pop(field)
        if 'action' in star_fields:
            star_fields['action'] = _join_action_items(star_fields['action'])
        return star_fields

    def create(self, validated_data):
        star_data = self._pop_star_data(validated_data)
        validated_data['user'] = self.context['request'].user
        if not validated_data.get('description') and star_data.get('situation'):
            validated_data['description'] = star_data['situation'][:120]
        portfolio = super().create(validated_data)
        if star_data:
            StarEntry.objects.create(portfolio=portfolio, **star_data)
        return portfolio

    def update(self, instance, validated_data):
        star_data = self._pop_star_data(validated_data)
        portfolio = super().update(instance, validated_data)
        if star_data:
            entry = portfolio.star_entries.order_by('id').first()
            if entry is None:
                StarEntry.objects.create(portfolio=portfolio, **star_data)
            else:
                for field, value in star_data.items():
                    setattr(entry, field, value)
                entry.save(update_fields=[*star_data.keys(), 'updated_at'])
        return portfolio
