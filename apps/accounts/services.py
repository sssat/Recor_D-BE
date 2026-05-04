import requests
from django.conf import settings
from django.db import transaction
from .models import User, SocialAccount


def kakao_login(code: str, redirect_uri: str = '') -> tuple[User, bool]:
    access_token = _exchange_code(code, redirect_uri)
    data = _get_user_info(access_token)

    social_id = str(data['id'])
    kakao_account = data.get('kakao_account', {})
    profile = kakao_account.get('profile', {})

    email = kakao_account.get('email', '') or f'kakao_{social_id}@kakao.local'

    return _get_or_create_user(
        social_id=social_id,
        email=email,
        name=profile.get('nickname', ''),
    )


def _exchange_code(code: str, redirect_uri: str) -> str:
    resp = requests.post(
        'https://kauth.kakao.com/oauth/token',
        data={
            'grant_type': 'authorization_code',
            'client_id': settings.KAKAO_REST_API_KEY,
            'redirect_uri': redirect_uri or settings.KAKAO_REDIRECT_URI,
            'code': code,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()['access_token']


def _get_user_info(access_token: str) -> dict:
    resp = requests.get(
        'https://kapi.kakao.com/v2/user/me',
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def _get_or_create_user(
    social_id: str, email: str, name: str
) -> tuple[User, bool]:
    with transaction.atomic():
        try:
            social = SocialAccount.objects.select_related('user').get(
                provider='kakao', social_id=social_id
            )
            user = social.user
            if name and user.name != name:
                user.name = name
                user.save(update_fields=['name'])
            return user, False
        except SocialAccount.DoesNotExist:
            pass

        user, created = User.objects.get_or_create(
            email=email,
            defaults={'username': email, 'name': name},
        )
        SocialAccount.objects.get_or_create(
            provider='kakao',
            social_id=social_id,
            defaults={'user': user},
        )
        return user, created
