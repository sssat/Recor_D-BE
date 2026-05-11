import json
import re

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.projects.models import Project
from core.ai.services import generate_star_portfolio_draft, generate_star_summary
from .models import Portfolio, StarEntry


def summarize_star_entry(entry: StarEntry) -> StarEntry:
    summary = generate_star_summary(
        situation=entry.situation,
        task=entry.task,
        action=entry.action,
        result=entry.result,
    )
    entry.ai_summary = summary
    entry.is_summarized = True
    entry.summarized_at = timezone.now()
    entry.save(update_fields=['ai_summary', 'is_summarized', 'summarized_at'])
    return entry


def _parse_json_response(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, flags=re.DOTALL)
        if not match:
            raise ValueError('AI 응답을 포트폴리오 형식으로 변환할 수 없습니다.')
        return json.loads(match.group(0))


def _normalize_list(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in re.split(r'[\n,]+', value) if item.strip()]
    return []


def _build_project_context(project):
    meetings = list(project.meetings.order_by('-date')[:5])
    todos = list(project.todos.order_by('-updated_at')[:10])
    schedules = list(project.schedules.order_by('-start_datetime')[:5])

    meeting_lines = [
        f"- {meeting.title}: {meeting.summary or meeting.ai_summary or meeting.transcript[:120]}"
        for meeting in meetings
    ]
    todo_lines = [
        f"- [{todo.status}] {todo.title}: {todo.description}"
        for todo in todos
    ]
    schedule_lines = [
        f"- {schedule.title}: {schedule.description}"
        for schedule in schedules
    ]

    return '\n'.join([
        f"프로젝트명: {project.name}",
        f"프로젝트 설명: {project.description}",
        f"기술/태그: {', '.join(project.tags)}",
        f"상태: {project.status}",
        '',
        '회의록:',
        '\n'.join(meeting_lines) or '- 없음',
        '',
        '할 일:',
        '\n'.join(todo_lines) or '- 없음',
        '',
        '일정:',
        '\n'.join(schedule_lines) or '- 없음',
    ])


def build_portfolio_draft_from_project(project):
    raw_result = generate_star_portfolio_draft(_build_project_context(project))
    data = _parse_json_response(raw_result)

    required_fields = ('title', 'situation', 'task', 'action', 'result')
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        raise ValueError(f"AI 응답에 필수 항목이 없습니다: {', '.join(missing_fields)}")

    return {
        'title': str(data['title']).strip(),
        'summary': str(data.get('summary') or data['situation'])[:240],
        'keywords': _normalize_list(data.get('keywords')) or project.tags[:3],
        'situation': str(data['situation']).strip(),
        'task': str(data['task']).strip(),
        'action': _normalize_list(data['action']),
        'result': str(data['result']).strip(),
    }


@transaction.atomic
def generate_portfolio_for_project(user, project_id):
    project = get_object_or_404(Project, id=project_id, owner=user)
    draft = build_portfolio_draft_from_project(project)

    portfolio = Portfolio.objects.create(
        user=user,
        project=project,
        title=draft['title'],
        description=draft['summary'],
        tech_stack=draft['keywords'],
    )
    StarEntry.objects.create(
        portfolio=portfolio,
        situation=draft['situation'],
        task=draft['task'],
        action='\n'.join(draft['action']),
        result=draft['result'],
    )
    return portfolio
