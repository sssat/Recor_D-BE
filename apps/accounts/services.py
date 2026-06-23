import logging

import requests
from django.conf import settings
from django.db import transaction
from .models import User, SocialAccount

logger = logging.getLogger(__name__)

_kakao_session = requests.Session()
_kakao_session.trust_env = False


def kakao_login(code: str, redirect_uri: str = '') -> tuple[User, bool]:
    access_token = _exchange_code(code, redirect_uri)
    data = _get_user_info(access_token)

    social_id = str(data['id'])
    kakao_account = data.get('kakao_account', {})
    profile = kakao_account.get('profile', {})
    properties = data.get('properties', {})
    logger.info(
        "Kakao account fields: has_email=%s, email_needs_agreement=%s, has_profile=%s, has_nickname=%s",
        kakao_account.get('has_email'),
        kakao_account.get('email_needs_agreement'),
        kakao_account.get('profile') is not None,
        profile.get('nickname') is not None,
    )

    email = kakao_account.get('email', '').strip()
    fallback_email = f'kakao_{social_id}@kakao.local'

    return _get_or_create_user(
        social_id=social_id,
        email=email or fallback_email,
        name=profile.get('nickname', '') or properties.get('nickname', ''),
    )


def _exchange_code(code: str, redirect_uri: str) -> str:
    data = {
        'grant_type': 'authorization_code',
        'client_id': settings.KAKAO_REST_API_KEY,
        'redirect_uri': redirect_uri or settings.KAKAO_REDIRECT_URI,
        'code': code,
    }

    if settings.KAKAO_CLIENT_SECRET:
        data['client_secret'] = settings.KAKAO_CLIENT_SECRET

    resp = _kakao_session.post(
        'https://kauth.kakao.com/oauth/token',
        data=data,
        timeout=10,
    )
    if not resp.ok:
        logger.warning("Kakao token exchange failed: %s %s", resp.status_code, resp.text)
    resp.raise_for_status()
    return resp.json()['access_token']


def _get_user_info(access_token: str) -> dict:
    resp = _kakao_session.get(
        'https://kapi.kakao.com/v2/user/me',
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=10,
    )
    if not resp.ok:
        logger.warning("Kakao user info request failed: %s %s", resp.status_code, resp.text)
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
            update_fields = []

            if email and user.email.endswith('@kakao.local') and user.email != email:
                user.email = email
                user.username = email
                update_fields.extend(['email', 'username'])

            if name and user.name != name:
                user.name = name
                update_fields.append('name')

            if update_fields:
                user.save(update_fields=update_fields)

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
