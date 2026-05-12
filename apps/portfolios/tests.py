import pytest
from django.urls import reverse
from unittest.mock import patch
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.meetings.models import Meeting
from apps.projects.models import Project
from apps.todos.models import Todo
from .models import Portfolio, StarEntry


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
    return Project.objects.create(name='포트폴리오 관리 시스템', user=user, tags=['React', 'DRF'])


@pytest.fixture
def portfolio(db, user, project):
    portfolio = Portfolio.objects.create(
        user=user,
        project=project,
        title='프론트엔드 개발 역량',
        description='프로젝트 경험을 STAR 구조로 정리했습니다.',
        tech_stack=['React', 'UI/UX'],
    )
    StarEntry.objects.create(
        portfolio=portfolio,
        situation='프로젝트 기록이 여러 곳에 흩어져 있었습니다.',
        task='기록을 하나의 포트폴리오로 정리해야 했습니다.',
        action='회의록을 분석했습니다.\n완료된 할 일을 분류했습니다.',
        result='STAR 초안 작성 시간을 줄였습니다.',
    )
    return portfolio


@pytest.mark.django_db
class TestPortfolio:
    def test_create_portfolio_with_frontend_payload(self, client, user, project):
        client.force_authenticate(user=user)

        resp = client.post(reverse('portfolio-list'), {
            'projectId': project.id,
            'title': 'API 구현 경험',
            'summary': '회의록과 할 일을 바탕으로 STAR 초안을 만들었습니다.',
            'keywords': ['Django', 'AI', '협업'],
            'situation': '회의록과 할 일 데이터가 분리되어 있었습니다.',
            'task': '프론트 구조에 맞는 포트폴리오 API가 필요했습니다.',
            'action': ['serializer 응답 포맷을 맞췄습니다.', 'AI 생성 흐름을 분리했습니다.'],
            'result': '프론트에서 바로 사용할 수 있는 응답을 제공했습니다.',
        }, format='json')

        assert resp.status_code == 201, resp.data
        assert resp.data['projectId'] == project.id
        assert resp.data['project'] == project.name
        assert resp.data['summary'] == '회의록과 할 일을 바탕으로 STAR 초안을 만들었습니다.'
        assert resp.data['keywords'] == ['Django', 'AI', '협업']
        assert resp.data['action'] == ['serializer 응답 포맷을 맞췄습니다.', 'AI 생성 흐름을 분리했습니다.']
        assert Portfolio.objects.filter(user=user, project=project).count() == 1
        assert StarEntry.objects.count() == 1

    def test_list_only_my_portfolios(self, client, user, other_user, portfolio):
        Portfolio.objects.create(user=other_user, title='다른 사용자 포트폴리오')
        client.force_authenticate(user=user)

        resp = client.get(reverse('portfolio-list'))

        assert resp.status_code == 200
        assert len(resp.data['results']) == 1
        assert resp.data['results'][0]['id'] == portfolio.id

    def test_update_portfolio_star_fields(self, client, user, portfolio):
        client.force_authenticate(user=user)

        resp = client.patch(reverse('portfolio-detail', args=[portfolio.id]), {
            'title': '수정된 포트폴리오',
            'keywords': 'Django, API',
            'action': '권한 검증을 추가했습니다.\n테스트를 작성했습니다.',
        }, format='json')

        assert resp.status_code == 200, resp.data
        assert resp.data['title'] == '수정된 포트폴리오'
        assert resp.data['keywords'] == ['Django', 'API']
        assert resp.data['action'] == ['권한 검증을 추가했습니다.', '테스트를 작성했습니다.']

    def test_cannot_use_other_user_project(self, client, user, other_user):
        other_project = Project.objects.create(name='타인 프로젝트', user=other_user)
        client.force_authenticate(user=user)

        resp = client.post(reverse('portfolio-list'), {
            'projectId': other_project.id,
            'title': '권한 없는 포트폴리오',
        }, format='json')

        assert resp.status_code == 400

    def test_summarize_star_entry(self, client, user, portfolio):
        entry = portfolio.star_entries.first()
        client.force_authenticate(user=user)

        with patch('apps.portfolios.services.generate_star_summary', return_value='STAR 요약 결과'):
            resp = client.post(reverse('star-summarize', kwargs={
                'portfolio_id': portfolio.id,
                'pk': entry.id,
            }))

        assert resp.status_code == 200
        assert resp.data['aiSummary'] == 'STAR 요약 결과'
        assert resp.data['isSummarized'] is True

    def test_generate_portfolio_from_project_context(self, client, user, project):
        Meeting.objects.create(
            project=project,
            title='기획 회의',
            date='2026-05-01',
            summary='포트폴리오 API와 STAR 구조를 논의했습니다.',
            created_by=user,
        )
        Todo.objects.create(
            user=user,
            project=project,
            title='serializer 구현',
            status='done',
        )
        client.force_authenticate(user=user)

        ai_response = {
            'title': '회의록 기반 포트폴리오 자동화',
            'summary': '프로젝트 기록을 분석해 STAR 포트폴리오 초안을 생성했습니다.',
            'keywords': ['Django', 'Gemini', 'STAR'],
            'situation': '프로젝트 기록이 회의록과 할 일로 나뉘어 있었습니다.',
            'task': '기록을 포트폴리오 초안으로 변환해야 했습니다.',
            'action': ['프로젝트 관련 데이터를 수집했습니다.', 'Gemini 응답을 STAR 구조로 변환했습니다.'],
            'result': '포트폴리오 초안 생성 흐름을 구현했습니다.',
        }

        with patch('apps.portfolios.services.generate_star_portfolio_draft', return_value=__import__('json').dumps(ai_response)):
            resp = client.post(reverse('portfolio-generate'), {
                'projectId': project.id,
            }, format='json')

        assert resp.status_code == 201, resp.data
        assert resp.data['title'] == '회의록 기반 포트폴리오 자동화'
        assert resp.data['keywords'] == ['Django', 'Gemini', 'STAR']
        assert resp.data['action'] == ['프로젝트 관련 데이터를 수집했습니다.', 'Gemini 응답을 STAR 구조로 변환했습니다.']
