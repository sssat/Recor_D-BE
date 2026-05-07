from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/', include('apps.accounts.urls')),
    path('api/projects/', include('apps.projects.urls')),
    path('api/todos/', include('apps.todos.urls')),
    path('api/schedules/', include('apps.schedules.urls')),
    path('api/meetings/', include('apps.meetings.urls')),
    path('api/portfolios/', include('apps.portfolios.urls')),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
