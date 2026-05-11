import pytest
from django.urls import reverse
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.projects.models import Project
from .models import Meeting


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email='user@test.com', username='user@test.com', password='pass')


@pytest.fixture
def meeting(db, user):
    return Meeting.objects.create(
        title='Sprint Retro',
        date='2026-05-01',
        created_by=user,
    )


@pytest.mark.django_db
class TestMeetingSummarize:
    def test_summarize_meeting(self, client, user, meeting):
        meeting.transcript = '회의 내용입니다.'
        meeting.save()
        client.force_authenticate(user=user)

        with patch('apps.meetings.services.summarize_meeting_note', return_value='AI 요약 결과'):
            resp = client.post(reverse('meeting-summarize', kwargs={'pk': meeting.id}))

        assert resp.status_code == 200
        assert resp.data['ai_summary'] == 'AI 요약 결과'
        assert resp.data['is_summarized'] is True

    def test_summarize_without_content(self, client, user, meeting):
        client.force_authenticate(user=user)
        resp = client.post(reverse('meeting-summarize', kwargs={'pk': meeting.id}))
        assert resp.status_code == 400

    def test_create_meeting(self, client, user):
        client.force_authenticate(user=user)
        resp = client.post(reverse('meeting-list'), {
            'title': '기획 회의',
            'date': '2026-05-01',
            'participants': '김철수, 이영희',
            'duration': '45분',
        })
        assert resp.status_code == 201, resp.data
        assert resp.data['title'] == '기획 회의'
        assert resp.data['participants'] == ['김철수', '이영희']
        assert resp.data['durationMinutes'] == 45

    def test_create_meeting_with_frontend_payload(self, client, user):
        project = Project.objects.create(name='포트폴리오 관리 시스템', owner=user)
        client.force_authenticate(user=user)

        resp = client.post(reverse('meeting-list'), {
            'project': project.name,
            'title': 'API 명세 점검',
            'date': '2026-05-02',
            'durationMinutes': 40,
            'participants': ['김철수', '박정연'],
            'summary': '회의록 API 요청과 응답 필드를 정리했습니다.',
            'tags': ['API', '회의록'],
            'transcript': '회의 내용입니다.',
            'keyPoints': ['목록 응답 필드 분리', '프로젝트 이름 포함'],
            'actionItems': ['API 명세 공유', '프론트 연동 확인'],
            'actionItemChecks': [True, False],
            'sourceType': 'manual',
            'audioFileName': '',
        }, format='json')

        assert resp.status_code == 201
        assert resp.data['project'] == project.name
        assert resp.data['projectId'] == project.id
        assert resp.data['durationMinutes'] == 40
        assert resp.data['keyPoints'] == ['목록 응답 필드 분리', '프로젝트 이름 포함']
        assert resp.data['actionItems'] == ['API 명세 공유', '프론트 연동 확인']
        assert resp.data['actionItemChecks'] == [True, False]
        assert resp.data['sourceType'] == 'manual'

    def test_get_meeting_projects(self, client, user):
        project = Project.objects.create(name='캡스톤 디자인', owner=user)
        Meeting.objects.create(
            project=project,
            title='프로젝트 회의',
            date='2026-05-03',
            created_by=user,
        )

        client.force_authenticate(user=user)
        resp = client.get(reverse('meeting-project-list'))

        assert resp.status_code == 200
        assert resp.data == [project.name]

    def test_create_draft_from_audio_uses_stt_and_summary(self, client, user):
        client.force_authenticate(user=user)
        audio_file = SimpleUploadedFile(
            'planning.mp3',
            b'audio-bytes',
            content_type='audio/mpeg',
        )

        with patch('apps.meetings.services.transcribe_audio_file', return_value='회의 원문 내용입니다.'), \
             patch(
                 'apps.meetings.services.summarize_meeting_note',
                 return_value='**주요 결정 사항**\n- API를 연동한다\n\n**액션 아이템**\n- STT 테스트를 작성한다',
             ):
            resp = client.post(reverse('meeting-draft-from-audio'), {
                'file': audio_file,
                'project': '포트폴리오 관리 시스템',
            }, format='multipart')

        assert resp.status_code == 200
        assert resp.data['project'] == '포트폴리오 관리 시스템'
        assert resp.data['title'] == 'planning 회의'
        assert resp.data['transcript'] == '회의 원문 내용입니다.'
        assert resp.data['summary'].startswith('**주요 결정 사항**')
        assert resp.data['keyPoints'] == ['API를 연동한다']
        assert resp.data['actionItems'] == ['STT 테스트를 작성한다']
        assert resp.data['actionItemChecks'] == [False]
        assert resp.data['sourceType'] == 'upload'
        assert resp.data['audioFileName'] == 'planning.mp3'
