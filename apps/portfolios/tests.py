from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.meetings.models import Meeting
from apps.projects.models import Project
from apps.todos.models import Todo
from .models import Portfolio, StarEntry


PORTFOLIO_SNAKE_CASE_RESPONSE_FIELDS = {
    'tech_stack',
    'github_url',
    'deploy_url',
    'thumbnail_url',
    'is_public',
    'star_entries',
    'created_at',
    'updated_at',
}
STAR_ENTRY_SNAKE_CASE_RESPONSE_FIELDS = {
    'ai_summary',
    'is_summarized',
    'summarized_at',
    'created_at',
}


def assert_no_snake_case_response_fields(data, snake_case_fields):
    assert not snake_case_fields.intersection(data.keys())


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='user@test.com',
        username='user@test.com',
        password='pass',
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        email='other@test.com',
        username='other@test.com',
        password='pass',
    )


@pytest.fixture
def project(db, user):
    return Project.objects.create(
        name='Portfolio manager',
        description='A project for turning records into portfolio drafts.',
        user=user,
        tags=['React', 'DRF'],
    )


@pytest.fixture
def portfolio(db, user, project):
    portfolio = Portfolio.objects.create(
        user=user,
        project=project,
        title='Portfolio API improvement',
        description='Organized project experience in STAR format.',
        tech_stack=['React', 'UI/UX'],
    )
    StarEntry.objects.create(
        portfolio=portfolio,
        situation='Project records were scattered across several pages.',
        task='Turn the records into one portfolio story.',
        action='Analyzed meeting logs.\nGrouped completed tasks.',
        result='Reduced the time needed to draft a portfolio entry.',
    )
    return portfolio


@pytest.mark.django_db
class TestPortfolio:
    def test_create_portfolio_with_frontend_payload(self, client, user, project):
        client.force_authenticate(user=user)

        resp = client.post(reverse('portfolio-list'), {
            'projectId': project.id,
            'title': 'API implementation experience',
            'summary': 'Created a STAR draft from meeting logs and tasks.',
            'keywords': ['Django', 'AI', 'Collaboration'],
            'situation': 'Meeting logs and tasks were managed separately.',
            'task': 'The frontend needed one portfolio-shaped API response.',
            'action': [
                'Aligned serializer response fields with the frontend.',
                'Separated AI draft generation from manual editing.',
            ],
            'result': 'The frontend can render the draft without field mapping.',
        }, format='json')

        assert resp.status_code == 201, resp.data
        assert resp.data['projectId'] == project.id
        assert resp.data['project'] == project.name
        assert resp.data['summary'] == 'Created a STAR draft from meeting logs and tasks.'
        assert resp.data['keywords'] == ['Django', 'AI', 'Collaboration']
        assert resp.data['action'] == [
            'Aligned serializer response fields with the frontend.',
            'Separated AI draft generation from manual editing.',
        ]
        assert resp.data['starEntries'][0]['action'] == resp.data['action']
        assert_no_snake_case_response_fields(resp.data, PORTFOLIO_SNAKE_CASE_RESPONSE_FIELDS)
        assert_no_snake_case_response_fields(
            resp.data['starEntries'][0],
            STAR_ENTRY_SNAKE_CASE_RESPONSE_FIELDS,
        )
        assert Portfolio.objects.filter(user=user, project=project).count() == 1
        assert StarEntry.objects.count() == 1

    def test_list_only_my_portfolios(self, client, user, other_user, portfolio):
        Portfolio.objects.create(user=other_user, title='Other user portfolio')
        client.force_authenticate(user=user)

        resp = client.get(reverse('portfolio-list'))

        assert resp.status_code == 200
        assert len(resp.data['results']) == 1
        assert resp.data['results'][0]['id'] == portfolio.id
        assert resp.data['results'][0]['summary'] == portfolio.description
        assert resp.data['results'][0]['keywords'] == portfolio.tech_stack
        assert_no_snake_case_response_fields(
            resp.data['results'][0],
            PORTFOLIO_SNAKE_CASE_RESPONSE_FIELDS,
        )

    def test_update_portfolio_star_fields(self, client, user, portfolio):
        client.force_authenticate(user=user)

        resp = client.patch(reverse('portfolio-detail', args=[portfolio.id]), {
            'title': 'Updated portfolio',
            'keywords': 'Django, API',
            'action': 'Added permission checks.\nWrote API contract tests.',
        }, format='json')

        assert resp.status_code == 200, resp.data
        assert resp.data['title'] == 'Updated portfolio'
        assert resp.data['keywords'] == ['Django', 'API']
        assert resp.data['action'] == [
            'Added permission checks.',
            'Wrote API contract tests.',
        ]
        assert_no_snake_case_response_fields(resp.data, PORTFOLIO_SNAKE_CASE_RESPONSE_FIELDS)

    def test_cannot_use_other_user_project(self, client, user, other_user):
        other_project = Project.objects.create(name='Other project', user=other_user)
        client.force_authenticate(user=user)

        resp = client.post(reverse('portfolio-list'), {
            'projectId': other_project.id,
            'title': 'Portfolio without access',
        }, format='json')

        assert resp.status_code == 400

    def test_summarize_star_entry(self, client, user, portfolio):
        entry = portfolio.star_entries.first()
        client.force_authenticate(user=user)

        with patch('apps.portfolios.services.generate_star_summary', return_value='STAR summary'):
            resp = client.post(reverse('star-summarize', kwargs={
                'portfolio_id': portfolio.id,
                'pk': entry.id,
            }))

        assert resp.status_code == 200
        assert resp.data['aiSummary'] == 'STAR summary'
        assert resp.data['isSummarized'] is True
        assert_no_snake_case_response_fields(resp.data, STAR_ENTRY_SNAKE_CASE_RESPONSE_FIELDS)

    def test_generate_portfolio_from_project_context(self, client, user, project):
        Meeting.objects.create(
            project=project,
            title='Planning meeting',
            date='2026-05-01',
            summary='Discussed the portfolio API and STAR structure.',
            created_by=user,
        )
        Todo.objects.create(
            user=user,
            project=project,
            title='Implement serializer',
            status='done',
        )
        client.force_authenticate(user=user)

        ai_response = {
            'title': 'Meeting-based portfolio automation',
            'summary': 'Generated a STAR portfolio draft from project records.',
            'keywords': ['Django', 'Gemini', 'STAR'],
            'situation': 'Project records were split between meetings and todos.',
            'task': 'Transform records into a portfolio draft.',
            'action': [
                'Collected project-related data.',
                'Normalized the AI response into STAR fields.',
            ],
            'result': 'Implemented a portfolio draft generation flow.',
        }

        with patch(
            'apps.portfolios.services.generate_star_portfolio_draft',
            return_value=__import__('json').dumps(ai_response),
        ):
            resp = client.post(reverse('portfolio-generate'), {
                'projectId': project.id,
            }, format='json')

        assert resp.status_code == 201, resp.data
        assert resp.data['title'] == 'Meeting-based portfolio automation'
        assert resp.data['keywords'] == ['Django', 'Gemini', 'STAR']
        assert resp.data['action'] == [
            'Collected project-related data.',
            'Normalized the AI response into STAR fields.',
        ]
        assert_no_snake_case_response_fields(resp.data, PORTFOLIO_SNAKE_CASE_RESPONSE_FIELDS)
