from django.urls import path
from .views import (
    PortfolioGenerateView, PortfolioListCreateView, PortfolioDetailView,
    StarEntryListCreateView, StarEntryDetailView, StarEntrySummarizeView,
)

urlpatterns = [
    path('', PortfolioListCreateView.as_view(), name='portfolio-list'),
    path('generate/', PortfolioGenerateView.as_view(), name='portfolio-generate'),
    path('<int:pk>/', PortfolioDetailView.as_view(), name='portfolio-detail'),
    path('<int:portfolio_id>/star/', StarEntryListCreateView.as_view(), name='star-list'),
    path('<int:portfolio_id>/star/<int:pk>/', StarEntryDetailView.as_view(), name='star-detail'),
    path('<int:portfolio_id>/star/<int:pk>/summarize/', StarEntrySummarizeView.as_view(), name='star-summarize'),
]
