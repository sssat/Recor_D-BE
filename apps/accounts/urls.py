from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import KakaoLoginView, LogoutView, ProfileView, WithdrawView

urlpatterns = [
    path('kakao/', KakaoLoginView.as_view(), name='kakao-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('withdraw/', WithdrawView.as_view(), name='withdraw'),
]
