import requests as http_requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer

from .serializers import KakaoLoginSerializer, SocialLoginResponseSerializer, UserSerializer
from .services import kakao_login


class KakaoLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Auth'],
        summary='카카오 로그인',
        description=(
            '카카오 인가코드를 받아 JWT를 발급합니다.\n\n'
            '**흐름**\n'
            '1. 프론트에서 Kakao SDK로 인가코드 수령\n'
            '2. 인가코드 + redirect_uri를 이 API에 전달\n'
            '3. 서버에서 카카오 토큰 교환 → 사용자 정보 조회 → JWT 반환\n\n'
            '**JWT 유효기간**\n'
            '- access: 24시간\n'
            '- refresh: 30일'
        ),
        request=KakaoLoginSerializer,
        responses={
            200: SocialLoginResponseSerializer,
            400: OpenApiResponse(description='인가코드 검증 실패'),
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
        except http_requests.RequestException:
            return Response({'error': '카카오 로그인에 실패했습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'is_new_user': is_new,
        })


class LogoutView(APIView):
    @extend_schema(
        tags=['Auth'],
        summary='로그아웃',
        description='리프레시 토큰을 블랙리스트에 추가합니다.',
        request=inline_serializer(
            name='LogoutRequest',
            fields={'refresh': serializers.CharField(help_text='리프레시 토큰')},
        ),
        responses={
            204: OpenApiResponse(description='로그아웃 성공'),
            400: OpenApiResponse(description='리프레시 토큰 누락 또는 유효하지 않음'),
        },
    )
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': '리프레시 토큰이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response({'error': '유효하지 않은 토큰입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=['Auth'], summary='내 프로필 조회', responses={200: UserSerializer})
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        tags=['Auth'],
        summary='내 프로필 수정',
        description='`name` 수정 가능.',
        request=UserSerializer,
        responses={200: UserSerializer},
    )
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
