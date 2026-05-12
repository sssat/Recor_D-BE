from rest_framework import serializers

from .models import Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = (
            'id', 'project', 'title', 'description', 'type',
            'color', 'start_datetime', 'end_datetime', 'is_all_day',
            'location', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate(self, attrs):
        start_datetime = attrs.get('start_datetime')
        end_datetime = attrs.get('end_datetime')
        if start_datetime and end_datetime and start_datetime >= end_datetime:
            raise serializers.ValidationError('End datetime must be after start datetime.')
        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
