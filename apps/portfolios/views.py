from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, serializers, status
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Portfolio, StarEntry
from .serializers import PortfolioSerializer, StarEntrySerializer
from .services import generate_portfolio_for_project, summarize_star_entry


PORTFOLIOS_TAG = ['portfolios']


class PortfolioGenerateSerializer(serializers.Serializer):
    projectId = serializers.IntegerField()


@extend_schema_view(
    get=extend_schema(tags=PORTFOLIOS_TAG),
    post=extend_schema(tags=PORTFOLIOS_TAG),
)
class PortfolioListCreateView(generics.ListCreateAPIView):
    serializer_class = PortfolioSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Portfolio.objects.none()

        qs = (
            Portfolio.objects.filter(user=self.request.user)
            .select_related('project')
            .prefetch_related('star_entries')
        )
        project = self.request.query_params.get('project') or self.request.query_params.get('projectId')
        query = self.request.query_params.get('q') or self.request.query_params.get('search')

        if project:
            project_filter = Q(project__name=project)
            if project.isdigit():
                project_filter |= Q(project_id=project)
            qs = qs.filter(project_filter)
        if query:
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(tech_stack__icontains=query)
                | Q(project__name__icontains=query)
                | Q(star_entries__situation__icontains=query)
                | Q(star_entries__task__icontains=query)
                | Q(star_entries__action__icontains=query)
                | Q(star_entries__result__icontains=query)
            ).distinct()

        return qs


@extend_schema_view(
    get=extend_schema(tags=PORTFOLIOS_TAG),
    put=extend_schema(tags=PORTFOLIOS_TAG),
    patch=extend_schema(tags=PORTFOLIOS_TAG),
    delete=extend_schema(tags=PORTFOLIOS_TAG),
)
class PortfolioDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PortfolioSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Portfolio.objects.none()

        return (
            Portfolio.objects.filter(user=self.request.user)
            .select_related('project')
            .prefetch_related('star_entries')
        )


@extend_schema_view(
    get=extend_schema(tags=PORTFOLIOS_TAG),
    post=extend_schema(tags=PORTFOLIOS_TAG),
)
class StarEntryListCreateView(generics.ListCreateAPIView):
    serializer_class = StarEntrySerializer

    def get_portfolio(self):
        if not hasattr(self, '_portfolio'):
            self._portfolio = get_object_or_404(
                Portfolio,
                id=self.kwargs['portfolio_id'],
                user=self.request.user,
            )
        return self._portfolio

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return StarEntry.objects.none()

        return StarEntry.objects.filter(portfolio=self.get_portfolio())

    def perform_create(self, serializer):
        serializer.save(portfolio=self.get_portfolio())


@extend_schema_view(
    get=extend_schema(tags=PORTFOLIOS_TAG),
    put=extend_schema(tags=PORTFOLIOS_TAG),
    patch=extend_schema(tags=PORTFOLIOS_TAG),
    delete=extend_schema(tags=PORTFOLIOS_TAG),
)
class StarEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StarEntrySerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return StarEntry.objects.none()

        return StarEntry.objects.filter(portfolio__user=self.request.user)


class StarEntrySummarizeView(APIView):
    serializer_class = StarEntrySerializer

    @extend_schema(tags=PORTFOLIOS_TAG, request=None, responses=StarEntrySerializer)
    def post(self, request, portfolio_id, pk):
        entry = get_object_or_404(
            StarEntry,
            id=pk,
            portfolio_id=portfolio_id,
            portfolio__user=request.user,
        )
        entry = summarize_star_entry(entry)
        return Response(StarEntrySerializer(entry).data)


@extend_schema(
    tags=PORTFOLIOS_TAG,
    request=PortfolioGenerateSerializer,
    responses=PortfolioSerializer,
)
class PortfolioGenerateView(APIView):
    serializer_class = PortfolioGenerateSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            portfolio = generate_portfolio_for_project(
                request.user,
                serializer.validated_data['projectId'],
            )
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            PortfolioSerializer(portfolio, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )
