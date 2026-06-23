from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    dateJoined = serializers.DateTimeField(source='date_joined', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'dateJoined')
        read_only_fields = ('id', 'email', 'dateJoined')


class KakaoLoginSerializer(serializers.Serializer):
    code = serializers.CharField(help_text='Kakao authorization code')
    redirect_uri = serializers.CharField(
        required=False,
        default='',
        help_text='Redirect URI used to issue the Kakao authorization code',
    )


class SocialLoginResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    access = serializers.CharField(help_text='JWT access token')
    refresh = serializers.CharField(help_text='JWT refresh token')
    isNewUser = serializers.BooleanField(help_text='Whether this is a new user')
