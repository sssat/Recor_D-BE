from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView
from rest_framework.response import Response

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
        return Meeting.objects.filter(created_by=self.request.user).select_related('project')


@extend_schema_view(
    get=extend_schema(tags=MEETINGS_TAG),
)
class MeetingProjectsView(APIView):
    def get(self, request):
        project_names = list(
            Meeting.objects.filter(created_by=request.user, project__isnull=False)
            .order_by('project__name')
            .values_list('project__name', flat=True)
            .distinct()
        )
        return Response(project_names)


@extend_schema_view(
    post=extend_schema(tags=MEETINGS_TAG),
)
class MeetingDraftFromAudioView(APIView):
    def post(self, request):
        serializer = MeetingDraftUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            draft = build_meeting_draft_from_audio(
                serializer.validated_data['file'],
                serializer.validated_data.get('project', ''),
            )
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(draft)


@extend_schema_view(
    post=extend_schema(tags=MEETINGS_TAG),
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
