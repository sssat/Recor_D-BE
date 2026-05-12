import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.filters import OrderingFilter

from .models import Todo
from .serializers import TodoSerializer


class TodoFilter(django_filters.FilterSet):
    due_date_after = django_filters.DateFilter(field_name='due_date', lookup_expr='gte')
    due_date_before = django_filters.DateFilter(field_name='due_date', lookup_expr='lte')

    class Meta:
        model = Todo
        fields = ['status', 'priority', 'project', 'due_date']


@extend_schema_view(
    get=extend_schema(
        tags=['Todos'],
        summary='할 일 목록 조회',
        description=(
            '로그인한 사용자의 할 일 목록을 조회합니다. '
            '`status`, `priority`, `project`, `due_date`로 필터링할 수 있고, '
            '`due_date_after`와 `due_date_before`로 날짜 기준 조회를 할 수 있습니다.'
        ),
        responses={200: TodoSerializer(many=True)},
    ),
    post=extend_schema(
        tags=['Todos'],
        summary='할 일 생성',
        description='새 할 일을 생성합니다. 프로젝트는 선택값이며, 기본 상태는 `in_progress`입니다.',
        responses={201: TodoSerializer, 400: OpenApiResponse(description='유효성 검사 실패')},
    ),
)
class TodoListCreateView(generics.ListCreateAPIView):
    serializer_class = TodoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = TodoFilter
    ordering_fields = ['due_date', 'priority', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Todo.objects.none()
        return Todo.objects.filter(user=self.request.user).select_related('project')


@extend_schema_view(
    get=extend_schema(
        tags=['Todos'],
        summary='할 일 상세 조회',
        responses={200: TodoSerializer, 404: OpenApiResponse(description='할 일을 찾을 수 없음')},
    ),
    put=extend_schema(
        tags=['Todos'],
        summary='할 일 전체 수정',
        responses={
            200: TodoSerializer,
            400: OpenApiResponse(description='유효성 검사 실패'),
            404: OpenApiResponse(description='할 일을 찾을 수 없음'),
        },
    ),
    patch=extend_schema(
        tags=['Todos'],
        summary='할 일 부분 수정',
        description='완료 처리는 `status`를 `done`으로, 완료 해제는 `in_progress`로 변경합니다.',
        responses={
            200: TodoSerializer,
            400: OpenApiResponse(description='유효성 검사 실패'),
            404: OpenApiResponse(description='할 일을 찾을 수 없음'),
        },
    ),
    delete=extend_schema(
        tags=['Todos'],
        summary='할 일 삭제',
        responses={
            204: OpenApiResponse(description='삭제 성공'),
            404: OpenApiResponse(description='할 일을 찾을 수 없음'),
        },
    ),
)
class TodoDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TodoSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Todo.objects.none()
        return Todo.objects.filter(user=self.request.user)
