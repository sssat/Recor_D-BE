from rest_framework import generics
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .models import Project
from .serializers import ProjectSerializer


@extend_schema_view(
    get=extend_schema(
        tags=['Projects'],
        summary='프로젝트 목록 조회',
        description='내 프로젝트 목록을 최신순으로 반환합니다.',
        responses={200: ProjectSerializer(many=True)},
    ),
    post=extend_schema(
        tags=['Projects'],
        summary='프로젝트 생성',
        description=(
            '새 프로젝트를 생성합니다.\n\n'
            '**status 값:** `inProgress` · `completed` · `planning`\n\n'
            '**colorKey 값:** `green` · `blue` · `teal` · `yellow` · `brightGreen` · `red`\n\n'
            '`meetingIds` · `todoIds` · `scheduleIds` 를 함께 보내면 해당 항목들이 이 프로젝트에 연결됩니다.'
        ),
        responses={
            201: ProjectSerializer,
            400: OpenApiResponse(description='유효성 검사 실패'),
        },
    ),
)
class ProjectListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return Project.objects.filter(
            user=self.request.user
        ).prefetch_related('meetings', 'todos', 'schedules').order_by('-created_at')


@extend_schema_view(
    get=extend_schema(
        tags=['Projects'],
        summary='프로젝트 상세 조회',
        responses={
            200: ProjectSerializer,
            404: OpenApiResponse(description='프로젝트를 찾을 수 없음'),
        },
    ),
    put=extend_schema(
        tags=['Projects'],
        summary='프로젝트 전체 수정',
        responses={
            200: ProjectSerializer,
            400: OpenApiResponse(description='유효성 검사 실패'),
            404: OpenApiResponse(description='프로젝트를 찾을 수 없음'),
        },
    ),
    patch=extend_schema(
        tags=['Projects'],
        summary='프로젝트 부분 수정',
        description='변경할 필드만 보내면 됩니다. `meetingIds` · `todoIds` · `scheduleIds` 를 보내면 연결 항목이 교체됩니다.',
        responses={
            200: ProjectSerializer,
            400: OpenApiResponse(description='유효성 검사 실패'),
            404: OpenApiResponse(description='프로젝트를 찾을 수 없음'),
        },
    ),
    delete=extend_schema(
        tags=['Projects'],
        summary='프로젝트 삭제',
        responses={
            204: OpenApiResponse(description='삭제 성공'),
            404: OpenApiResponse(description='프로젝트를 찾을 수 없음'),
        },
    ),
)
class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return Project.objects.filter(
            user=self.request.user
        ).prefetch_related('meetings', 'todos', 'schedules')
