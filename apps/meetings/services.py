from django.utils import timezone

from core.ai.services import summarize_meeting_note, transcribe_audio_file
from .models import Meeting


MAX_AUDIO_FILE_SIZE = 25 * 1024 * 1024
SUPPORTED_AUDIO_EXTENSIONS = {'mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm'}


def summarize_meeting(meeting: Meeting) -> Meeting:
    content = meeting.transcript or meeting.summary
    summary = summarize_meeting_note(content)
    meeting.ai_summary = summary
    if not meeting.summary:
        meeting.summary = summary
    meeting.is_summarized = True
    meeting.summarized_at = timezone.now()
    meeting.save(update_fields=['summary', 'ai_summary', 'is_summarized', 'summarized_at'])
    return meeting


def validate_audio_file(file):
    extension = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''
    if extension not in SUPPORTED_AUDIO_EXTENSIONS:
        raise ValueError('MP3, MP4, MPEG, MPGA, M4A, WAV, WEBM 파일만 업로드할 수 있습니다.')
    if file.size > MAX_AUDIO_FILE_SIZE:
        raise ValueError('파일 용량은 25MB를 초과할 수 없습니다.')


def _parse_summary_sections(summary_text):
    key_points = []
    action_items = []
    current_section = None

    for raw_line in summary_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if '주요 결정' in line or '핵심' in line or '중요' in line:
            current_section = 'key_points'
            continue
        if '액션' in line or '할 일' in line or '해야 할' in line:
            current_section = 'action_items'
            continue
        if line.startswith(('-', '*', '•')):
            item = line.lstrip('-*•').strip()
            if current_section == 'action_items':
                action_items.append(item)
            elif current_section == 'key_points':
                key_points.append(item)

    if not key_points and summary_text:
        key_points = [summary_text.splitlines()[0].strip()[:200]]

    return key_points, action_items


def build_meeting_draft_from_audio(file, project=''):
    validate_audio_file(file)
    transcript = transcribe_audio_file(file)
    ai_summary = summarize_meeting_note(transcript) if transcript else ''
    key_points, action_items = _parse_summary_sections(ai_summary)
    cleaned_name = file.name.rsplit('.', 1)[0].replace('-', ' ').replace('_', ' ').strip()
    title = f'{cleaned_name} 회의' if cleaned_name else '새 회의록'
    selected_project = project.strip() if project else ''

    return {
        'project': selected_project,
        'title': title,
        'date': timezone.localdate().isoformat(),
        'durationMinutes': 0,
        'participants': [],
        'summary': ai_summary,
        'tags': ['AI요약', '업로드'],
        'transcript': transcript,
        'keyPoints': key_points,
        'actionItems': action_items,
        'actionItemChecks': [False for _ in action_items],
        'sourceType': 'upload',
        'audioFileName': file.name,
    }
