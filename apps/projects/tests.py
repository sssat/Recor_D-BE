import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.todos.models import Todo
from apps.schedules.models import Schedule
from .models import Project, ProjectMember


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email='user@test.com', username='user@test.com', password='pass')


@pytest.fixture
def other_user(db):
    return User.objects.create_user(email='other@test.com', username='other@test.com', password='pass')


@pytest.fixture
def project(db, user):
    project = Project.objects.create(name='Test Project', user=user)
    ProjectMember.objects.create(project=project, user=user, role='owner')
    return project


@pytest.mark.django_db
class TestProject:
    def test_create_project(self, client, user):
        client.force_authenticate(user=user)
        resp = client.post(reverse('project-list'), {
            'name': 'New Project',
            'description': 'desc',
            'status': 'inProgress',
            'tags': ['React', 'Python'],
            'colorKey': 'green',
        }, format='json')
        assert resp.status_code == 201
        assert resp.data['status'] == 'inProgress'
        assert resp.data['colorKey'] == 'green'
        assert resp.data['meetingIds'] == []
        assert resp.data['todoIds'] == []
        assert resp.data['scheduleIds'] == []
        assert 'startDate' in resp.data
        assert 'endDate' in resp.data
        assert resp.data['progress'] == 0

    def test_list_only_my_projects(self, client, user, project, other_user):
        client.force_authenticate(user=other_user)
        resp = client.get(reverse('project-list'))
        assert resp.status_code == 200
        assert len(resp.data['results']) == 0

    def test_list_returns_my_projects(self, client, user, project):
        client.force_authenticate(user=user)
        resp = client.get(reverse('project-list'))
        assert resp.status_code == 200
        assert len(resp.data['results']) == 1
        assert resp.data['results'][0]['id'] == project.id

    def test_retrieve_project(self, client, user, project):
        client.force_authenticate(user=user)
        resp = client.get(reverse('project-detail', args=[project.id]))
        assert resp.status_code == 200
        assert resp.data['id'] == project.id
        assert resp.data['name'] == project.name

    def test_cannot_retrieve_other_user_project(self, client, other_user, project):
        client.force_authenticate(user=other_user)
        resp = client.get(reverse('project-detail', args=[project.id]))
        assert resp.status_code == 404

    def test_update_project(self, client, user, project):
        client.force_authenticate(user=user)
        resp = client.patch(reverse('project-detail', args=[project.id]), {
            'name': 'Updated Name',
            'status': 'completed',
        }, format='json')
        assert resp.status_code == 200
        assert resp.data['name'] == 'Updated Name'
        assert resp.data['status'] == 'completed'

    def test_delete_project(self, client, user, project):
        client.force_authenticate(user=user)
        resp = client.delete(reverse('project-detail', args=[project.id]))
        assert resp.status_code == 204
        assert not Project.objects.filter(id=project.id).exists()

    def test_delete_project_unlinks_todos_and_schedules(self, client, user, project):
        todo = Todo.objects.create(user=user, project=project, title='할일')
        schedule = Schedule.objects.create(
            user=user, project=project, title='일정',
            start_datetime='2026-05-01T10:00:00Z',
            end_datetime='2026-05-01T11:00:00Z',
        )
        client.force_authenticate(user=user)
        client.delete(reverse('project-detail', args=[project.id]))

        todo.refresh_from_db()
        schedule.refresh_from_db()
        assert todo.project is None
        assert schedule.project is None

    def test_unauthenticated_cannot_access(self, client):
        resp = client.get(reverse('project-list'))
        assert resp.status_code == 401
