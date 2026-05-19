from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    dateJoined = serializers.DateTimeField(source='date_joined', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'dateJoined')
        read_only_fields = ('id', 'email', 'dateJoined')


class KakaoLoginSerializer(serializers.Serializer):
    code = serializers.CharField(help_text='카카오 인가코드')
    redirect_uri = serializers.CharField(
        required=False,
        default='',
        help_text='카카오 인가코드 발급 시 사용한 redirect_uri',
    )


class SocialLoginResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    access = serializers.CharField(help_text='JWT 액세스 토큰 (24시간 유효)')
    refresh = serializers.CharField(help_text='JWT 리프레시 토큰 (30일 유효)')
    isNewUser = serializers.BooleanField(help_text='최초 가입 여부')
