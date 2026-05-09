from django.urls import path
from .views import (
    MeetingDetailView,
    MeetingDraftFromAudioView,
    MeetingListCreateView,
    MeetingProjectsView,
    MeetingSummarizeView,
)

urlpatterns = [
    path('', MeetingListCreateView.as_view(), name='meeting-list'),
    path('projects/', MeetingProjectsView.as_view(), name='meeting-project-list'),
    path('draft-from-audio/', MeetingDraftFromAudioView.as_view(), name='meeting-draft-from-audio'),
    path('<int:pk>/', MeetingDetailView.as_view(), name='meeting-detail'),
    path('<int:pk>/summarize/', MeetingSummarizeView.as_view(), name='meeting-summarize'),
]
