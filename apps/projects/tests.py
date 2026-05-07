import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.accounts.models import User
from .models import Project, ProjectMember


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email='user@test.com', username='user@test.com', password='pass')


@pytest.fixture
def project(db, user):
    project = Project.objects.create(name='Test Project', owner=user)
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

    def test_list_only_my_projects(self, client, user, project):
        other = User.objects.create_user(email='other@test.com', username='other@test.com', password='pass')
        client.force_authenticate(user=other)
        resp = client.get(reverse('project-list'))
        assert resp.status_code == 200
        assert len(resp.data['results']) == 0
