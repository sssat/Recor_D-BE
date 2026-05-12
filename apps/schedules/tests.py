import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.schedules.models import Schedule


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email='user@test.com', username='user@test.com', password='pass')


@pytest.fixture
def other_user(db):
    return User.objects.create_user(email='other@test.com', username='other@test.com', password='pass')


@pytest.mark.django_db
class TestSchedule:
    def test_create_schedule(self, client, user):
        client.force_authenticate(user=user)
        resp = client.post(reverse('schedule-list'), {
            'title': 'Sprint Meeting',
            'type': 'meeting',
            'start_datetime': '2026-05-01T10:00:00+09:00',
            'end_datetime': '2026-05-01T11:00:00+09:00',
        })
        assert resp.status_code == 201
        assert resp.data['type'] == 'meeting'
        assert resp.data['color'] == 'green'
        assert 'updated_at' in resp.data

    def test_invalid_datetime_range(self, client, user):
        client.force_authenticate(user=user)
        resp = client.post(reverse('schedule-list'), {
            'title': 'Bad Schedule',
            'start_datetime': '2026-05-01T11:00:00+09:00',
            'end_datetime': '2026-05-01T10:00:00+09:00',
        })
        assert resp.status_code == 400

    def test_order_schedules_by_start_datetime(self, client, user):
        client.force_authenticate(user=user)
        client.post(reverse('schedule-list'), {
            'title': 'Later',
            'start_datetime': '2026-05-01T13:00:00+09:00',
            'end_datetime': '2026-05-01T14:00:00+09:00',
        })
        client.post(reverse('schedule-list'), {
            'title': 'Earlier',
            'start_datetime': '2026-05-01T10:00:00+09:00',
            'end_datetime': '2026-05-01T11:00:00+09:00',
        })
        resp = client.get(reverse('schedule-list'), {'ordering': 'start_datetime'})
        assert resp.status_code == 200
        assert [schedule['title'] for schedule in resp.data['results']] == ['Earlier', 'Later']

    def test_unauthenticated_cannot_access(self, client):
        resp = client.get(reverse('schedule-list'))
        assert resp.status_code == 401

    def test_list_only_my_schedules(self, client, user, other_user):
        Schedule.objects.create(
            user=user,
            title='My Schedule',
            start_datetime='2026-05-01T10:00:00+09:00',
            end_datetime='2026-05-01T11:00:00+09:00',
        )
        Schedule.objects.create(
            user=other_user,
            title='Other Schedule',
            start_datetime='2026-05-01T12:00:00+09:00',
            end_datetime='2026-05-01T13:00:00+09:00',
        )
        client.force_authenticate(user=user)

        resp = client.get(reverse('schedule-list'))

        assert resp.status_code == 200
        assert [schedule['title'] for schedule in resp.data['results']] == ['My Schedule']

    def test_cannot_retrieve_other_user_schedule(self, client, user, other_user):
        schedule = Schedule.objects.create(
            user=other_user,
            title='Other Schedule',
            start_datetime='2026-05-01T10:00:00+09:00',
            end_datetime='2026-05-01T11:00:00+09:00',
        )
        client.force_authenticate(user=user)

        resp = client.get(reverse('schedule-detail', args=[schedule.id]))

        assert resp.status_code == 404

    def test_retrieve_schedule(self, client, user):
        schedule = Schedule.objects.create(
            user=user,
            title='My Schedule',
            start_datetime='2026-05-01T10:00:00+09:00',
            end_datetime='2026-05-01T11:00:00+09:00',
        )
        client.force_authenticate(user=user)

        resp = client.get(reverse('schedule-detail', args=[schedule.id]))

        assert resp.status_code == 200
        assert resp.data['id'] == schedule.id
        assert resp.data['title'] == schedule.title

    def test_update_schedule(self, client, user):
        schedule = Schedule.objects.create(
            user=user,
            title='My Schedule',
            start_datetime='2026-05-01T10:00:00+09:00',
            end_datetime='2026-05-01T11:00:00+09:00',
        )
        client.force_authenticate(user=user)

        resp = client.patch(reverse('schedule-detail', args=[schedule.id]), {
            'title': 'Updated Schedule',
            'color': 'blue',
        }, format='json')

        assert resp.status_code == 200
        assert resp.data['title'] == 'Updated Schedule'
        assert resp.data['color'] == 'blue'

    def test_delete_schedule(self, client, user):
        schedule = Schedule.objects.create(
            user=user,
            title='My Schedule',
            start_datetime='2026-05-01T10:00:00+09:00',
            end_datetime='2026-05-01T11:00:00+09:00',
        )
        client.force_authenticate(user=user)

        resp = client.delete(reverse('schedule-detail', args=[schedule.id]))

        assert resp.status_code == 204
        assert not Schedule.objects.filter(id=schedule.id).exists()

    def test_filter_by_datetime_range(self, client, user):
        Schedule.objects.create(
            user=user,
            title='Inside Range',
            start_datetime='2026-05-01T10:00:00+09:00',
            end_datetime='2026-05-01T11:00:00+09:00',
        )
        Schedule.objects.create(
            user=user,
            title='Outside Range',
            start_datetime='2026-05-03T10:00:00+09:00',
            end_datetime='2026-05-03T11:00:00+09:00',
        )
        client.force_authenticate(user=user)

        resp = client.get(reverse('schedule-list'), {
            'start': '2026-05-01T00:00:00+09:00',
            'end': '2026-05-01T23:59:59+09:00',
        })

        assert resp.status_code == 200
        assert [schedule['title'] for schedule in resp.data['results']] == ['Inside Range']
