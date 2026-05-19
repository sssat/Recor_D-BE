import pytest
from django.urls import reverse
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from .models import User


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='test@example.com',
        username='test@example.com',
        password='testpass123',
        name='Test User',
    )


@pytest.mark.django_db
class TestKakaoLogin:
    def _mock_kakao(self, mock_post, mock_get, kakao_data):
        mock_post.return_value = MagicMock(
            json=lambda: {'access_token': 'fake-access-token'},
            raise_for_status=lambda: None,
        )
        mock_get.return_value = MagicMock(
            json=lambda: kakao_data,
            raise_for_status=lambda: None,
        )

    def test_login_with_email(self, client):
        kakao_data = {
            'id': 99999,
            'kakao_account': {
                'email': 'kakao@example.com',
                'profile': {'nickname': '카카오유저', 'profile_image_url': ''},
            },
        }
        with patch('apps.accounts.services.requests.post') as mp, \
             patch('apps.accounts.services.requests.get') as mg:
            self._mock_kakao(mp, mg, kakao_data)
            resp = client.post(reverse('kakao-login'), {'code': 'auth-code', 'redirect_uri': 'http://localhost:3000'})

        assert resp.status_code == 200
        assert resp.data['user']['email'] == 'kakao@example.com'
        assert resp.data['isNewUser'] is True
        assert 'access' in resp.data

    def test_login_without_email(self, client):
        kakao_data = {
            'id': 88888,
            'kakao_account': {
                'profile': {'nickname': '익명', 'profile_image_url': ''},
            },
        }
        with patch('apps.accounts.services.requests.post') as mp, \
             patch('apps.accounts.services.requests.get') as mg:
            self._mock_kakao(mp, mg, kakao_data)
            resp = client.post(reverse('kakao-login'), {'code': 'auth-code'})

        assert resp.status_code == 200
        assert resp.data['user']['email'] == 'kakao_88888@kakao.local'

    def test_returns_24h_access_token(self, client):
        from rest_framework_simplejwt.tokens import AccessToken
        kakao_data = {
            'id': 77777,
            'kakao_account': {
                'email': 'jwt@example.com',
                'profile': {'nickname': 'JWT유저', 'profile_image_url': ''},
            },
        }
        with patch('apps.accounts.services.requests.post') as mp, \
             patch('apps.accounts.services.requests.get') as mg:
            self._mock_kakao(mp, mg, kakao_data)
            resp = client.post(reverse('kakao-login'), {'code': 'auth-code'})

        token = AccessToken(resp.data['access'])
        assert token['exp'] - token['iat'] == 86400


@pytest.mark.django_db
class TestLogout:
    def test_logout_success(self, client, user):
        from rest_framework_simplejwt.tokens import RefreshToken as RT
        refresh = str(RT.for_user(user))
        client.force_authenticate(user=user)
        resp = client.post(reverse('logout'), {'refresh': refresh})
        assert resp.status_code == 204

    def test_logout_without_token_returns_400(self, client, user):
        client.force_authenticate(user=user)
        resp = client.post(reverse('logout'), {})
        assert resp.status_code == 400

    def test_logout_with_invalid_token_returns_400(self, client, user):
        client.force_authenticate(user=user)
        resp = client.post(reverse('logout'), {'refresh': 'invalid-token'})
        assert resp.status_code == 400


@pytest.mark.django_db
class TestProfile:
    def test_get_profile(self, client, user):
        client.force_authenticate(user=user)
        resp = client.get(reverse('profile'))
        assert resp.status_code == 200
        assert resp.data['email'] == user.email

    def test_patch_profile_name(self, client, user):
        client.force_authenticate(user=user)
        resp = client.patch(reverse('profile'), {'name': '새이름'})
        assert resp.status_code == 200
        assert resp.data['name'] == '새이름'

    def test_unauthenticated_cannot_access_profile(self, client):
        resp = client.get(reverse('profile'))
        assert resp.status_code == 401


@pytest.mark.django_db
class TestWithdraw:
    def test_withdraw_deletes_user(self, client, user):
        from rest_framework_simplejwt.tokens import RefreshToken as RT
        refresh = str(RT.for_user(user))
        client.force_authenticate(user=user)
        resp = client.delete(reverse('withdraw'), {'refresh': refresh})
        assert resp.status_code == 204
        assert not User.objects.filter(pk=user.pk).exists()

    def test_withdraw_without_refresh_token(self, client, user):
        client.force_authenticate(user=user)
        resp = client.delete(reverse('withdraw'), {})
        assert resp.status_code == 204
        assert not User.objects.filter(pk=user.pk).exists()

    def test_unauthenticated_cannot_withdraw(self, client):
        resp = client.delete(reverse('withdraw'))
        assert resp.status_code == 401
