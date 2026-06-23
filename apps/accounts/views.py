import requests as http_requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer

from .serializers import (
    KakaoLoginSerializer,
    SocialLoginResponseSerializer,
    UserSerializer,
)
from .services import kakao_login


class KakaoLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Auth'],
        summary='Kakao login',
        description='Exchange a Kakao authorization code for local JWT tokens.',
        request=KakaoLoginSerializer,
        responses={
            200: SocialLoginResponseSerializer,
            400: OpenApiResponse(description='Kakao authorization failed'),
        },
    )
    def post(self, request):
        serializer = KakaoLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user, is_new = kakao_login(
                code=serializer.validated_data['code'],
                redirect_uri=serializer.validated_data.get('redirect_uri', ''),
            )
        except http_requests.RequestException as exc:
            payload = {'error': 'Kakao login failed.'}

            if settings.DEBUG:
                payload['detail'] = str(exc)

                if exc.response is not None:
                    payload['detail'] = exc.response.text
                    payload['status_code'] = exc.response.status_code

            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'isNewUser': is_new,
        })


class LogoutView(APIView):
    @extend_schema(
        tags=['Auth'],
        summary='Logout',
        description='Blacklist the submitted refresh token.',
        request=inline_serializer(
            name='LogoutRequest',
            fields={'refresh': serializers.CharField(help_text='Refresh token')},
        ),
        responses={
            204: OpenApiResponse(description='Logged out'),
            400: OpenApiResponse(description='Missing or invalid refresh token'),
        },
    )
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response(
                {'error': 'Invalid token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=['Auth'], summary='Get profile', responses={200: UserSerializer})
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        tags=['Auth'],
        summary='Update profile',
        description='Update the current user profile.',
        request=UserSerializer,
        responses={200: UserSerializer},
    )
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class WithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Auth'],
        summary='Withdraw account',
        description='Delete the current user account and related data.',
        request=inline_serializer(
            name='WithdrawRequest',
            fields={
                'refresh': serializers.CharField(
                    help_text='Refresh token',
                    required=False,
                )
            },
        ),
        responses={
            204: OpenApiResponse(description='Account deleted'),
        },
    )
    def delete(self, request):
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass

        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
