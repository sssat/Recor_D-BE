from django.db.models import Q
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.projects.models import Project
from .models import Meeting
from .serializers import MeetingDraftUploadSerializer, MeetingSerializer
from .services import build_meeting_draft_from_audio, summarize_meeting


MEETINGS_TAG = ['meetings']


@extend_schema_view(
    get=extend_schema(tags=MEETINGS_TAG),
    post=extend_schema(tags=MEETINGS_TAG),
)
class MeetingListCreateView(generics.ListCreateAPIView):
    serializer_class = MeetingSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['project', 'date', 'source_type']
    ordering_fields = ['date', 'updated_at', 'created_at']
    ordering = ['-date', '-updated_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Meeting.objects.none()

        qs = Meeting.objects.filter(created_by=self.request.user).select_related('project')
        project = self.request.query_params.get('project')
        query = self.request.query_params.get('q') or self.request.query_params.get('search')

        if project:
            project_filter = Q(project__name=project)
            if project.isdigit():
                project_filter |= Q(project_id=project)
            qs = qs.filter(project_filter)
        if query:
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(transcript__icontains=query)
                | Q(project__name__icontains=query)
            )

        return qs


@extend_schema_view(
    get=extend_schema(tags=MEETINGS_TAG),
    put=extend_schema(tags=MEETINGS_TAG),
    patch=extend_schema(tags=MEETINGS_TAG),
    delete=extend_schema(tags=MEETINGS_TAG),
)
class MeetingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MeetingSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Meeting.objects.none()

        return Meeting.objects.filter(created_by=self.request.user).select_related('project')


@extend_schema_view(
    get=extend_schema(
        tags=MEETINGS_TAG,
        responses={200: {'type': 'array', 'items': {'type': 'string'}}},
    ),
)
class MeetingProjectsView(APIView):
    def get(self, request):
        owned_project_names = (
            Project.objects.filter(user=request.user)
            .order_by('name')
            .values_list('name', flat=True)
        )
        meeting_project_names = (
            Meeting.objects.filter(created_by=request.user, project__isnull=False)
            .order_by('project__name')
            .values_list('project__name', flat=True)
            .distinct()
        )
        project_names = list(dict.fromkeys([*owned_project_names, *meeting_project_names]))
        return Response(project_names)


@extend_schema_view(
    post=extend_schema(
        tags=MEETINGS_TAG,
        request=MeetingDraftUploadSerializer,
        responses=MeetingSerializer,
    ),
)
class MeetingDraftFromAudioView(APIView):
    def get_permissions(self):
        if self.request.method == 'OPTIONS':
            return []
        return super().get_permissions()

    def dispatch(self, request, *args, **kwargs):
        print(
            f'[meeting-audio] dispatch method={request.method} path={request.path}',
            flush=True,
        )
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        print('[meeting-audio] request received', flush=True)
        serializer = MeetingDraftUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            draft = build_meeting_draft_from_audio(
                serializer.validated_data['file'],
                serializer.validated_data.get('project', ''),
            )
        except ValueError as exc:
            print(f'[meeting-audio] validation failed: {exc}', flush=True)
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            print(f'[meeting-audio] failed: {type(exc).__name__}: {exc}', flush=True)
            payload = {'error': 'Failed to process the audio file.'}

            if settings.DEBUG:
                payload['detail'] = str(exc)

            return Response(payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        print('[meeting-audio] request finished', flush=True)
        return Response(draft)


@extend_schema_view(
    post=extend_schema(tags=MEETINGS_TAG, request=None, responses=MeetingSerializer),
)
class MeetingSummarizeView(APIView):
    def post(self, request, pk):
        meeting = Meeting.objects.filter(created_by=request.user).filter(pk=pk).first()
        if not meeting:
            return Response({'error': '회의록을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        if not meeting.transcript and not meeting.summary:
            return Response({'error': '요약할 내용이 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        meeting = summarize_meeting(meeting)
        return Response(MeetingSerializer(meeting, context={'request': request}).data)
