from django.utils.dateparse import parse_date, parse_datetime
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter

from .models import Schedule
from .serializers import ScheduleSerializer


def _parse_datetime_param(value, field_name):
    if parse_datetime(value) is None and parse_date(value) is None:
        raise ValidationError({
            field_name: '올바른 날짜 또는 일시 형식을 입력하세요. 예: 2026-01-01 또는 2026-01-01T00:00:00'
        })
    return value


@extend_schema_view(
    get=extend_schema(
        tags=['Schedules'],
        summary='일정 목록 조회',
        description=(
            '로그인한 사용자의 일정 목록을 조회합니다. '
            '`start`와 `end` 쿼리로 날짜 범위를 조회하고, '
            '`ordering=start_datetime`으로 시작일시 기준 정렬할 수 있습니다.'
        ),
        responses={200: ScheduleSerializer(many=True)},
    ),
    post=extend_schema(
        tags=['Schedules'],
        summary='일정 생성',
        description='새 일정을 생성합니다. 프로젝트는 선택값이며, 기본 색상은 `green`입니다.',
        responses={201: ScheduleSerializer, 400: OpenApiResponse(description='유효성 검사 실패')},
    ),
)
class ScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = ScheduleSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['project', 'is_all_day', 'type', 'color']
    ordering_fields = ['start_datetime', 'end_datetime', 'created_at']
    ordering = ['start_datetime']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Schedule.objects.none()
        qs = Schedule.objects.filter(user=self.request.user)
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')
        if start:
            qs = qs.filter(start_datetime__gte=_parse_datetime_param(start, 'start'))
        if end:
            qs = qs.filter(end_datetime__lte=_parse_datetime_param(end, 'end'))
        return qs.select_related('project')


@extend_schema_view(
    get=extend_schema(
        tags=['Schedules'],
        summary='일정 상세 조회',
        responses={200: ScheduleSerializer, 404: OpenApiResponse(description='일정을 찾을 수 없음')},
    ),
    put=extend_schema(
        tags=['Schedules'],
        summary='일정 전체 수정',
        responses={
            200: ScheduleSerializer,
            400: OpenApiResponse(description='유효성 검사 실패'),
            404: OpenApiResponse(description='일정을 찾을 수 없음'),
        },
    ),
    patch=extend_schema(
        tags=['Schedules'],
        summary='일정 부분 수정',
        responses={
            200: ScheduleSerializer,
            400: OpenApiResponse(description='유효성 검사 실패'),
            404: OpenApiResponse(description='일정을 찾을 수 없음'),
        },
    ),
    delete=extend_schema(
        tags=['Schedules'],
        summary='일정 삭제',
        responses={
            204: OpenApiResponse(description='삭제 성공'),
            404: OpenApiResponse(description='일정을 찾을 수 없음'),
        },
    ),
)
class ScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ScheduleSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Schedule.objects.none()
        return Schedule.objects.filter(user=self.request.user)
