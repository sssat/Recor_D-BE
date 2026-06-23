from django.utils import timezone

from core.ai.services import summarize_meeting_note, transcribe_audio_file
from .models import Meeting


MAX_AUDIO_FILE_SIZE = 50 * 1024 * 1024
SUPPORTED_AUDIO_EXTENSIONS = {'mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm'}


def _debug(message):
    print(f'[meeting-audio] {message}', flush=True)


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
        raise ValueError('Only MP3, MP4, MPEG, MPGA, M4A, WAV, and WEBM files are supported.')
    if file.size > MAX_AUDIO_FILE_SIZE:
        raise ValueError('The audio file is larger than 50MB.')


def _parse_summary_sections(summary_text):
    key_points = []
    action_items = []
    current_section = None

    for raw_line in summary_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        lower_line = line.lower()
        if any(keyword in lower_line for keyword in ('summary', 'key point', 'decision')):
            current_section = 'key_points'
            continue

        if any(keyword in lower_line for keyword in ('action', 'todo', 'checklist')):
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


def _build_fallback_summary(transcript):
    cleaned_transcript = ' '.join((transcript or '').split())
    if not cleaned_transcript:
        return ''
    return cleaned_transcript[:500]


def build_meeting_draft_from_audio(file, project=''):
    _debug(f'received file name={file.name} size={getattr(file, "size", "unknown")}')
    validate_audio_file(file)

    _debug('transcription start')
    transcript = transcribe_audio_file(file)
    _debug(f'transcription done chars={len(transcript or "")}')

    ai_summary = ''
    if transcript:
        try:
            _debug('summary start')
            ai_summary = summarize_meeting_note(transcript)
            _debug(f'summary done chars={len(ai_summary or "")}')
        except Exception as exc:
            _debug(f'summary failed: {type(exc).__name__}: {exc}')
            ai_summary = _build_fallback_summary(transcript)

    key_points, action_items = _parse_summary_sections(ai_summary)
    if transcript and not key_points:
        key_points = [_build_fallback_summary(transcript)]

    cleaned_name = file.name.rsplit('.', 1)[0].replace('-', ' ').replace('_', ' ').strip()
    title = f'{cleaned_name} meeting' if cleaned_name else 'New meeting note'
    selected_project = project.strip() if project else ''

    return {
        'project': selected_project,
        'title': title,
        'date': timezone.localdate().isoformat(),
        'durationMinutes': 0,
        'participants': [],
        'summary': ai_summary,
        'tags': ['AI summary', 'upload'],
        'transcript': transcript,
        'keyPoints': key_points,
        'actionItems': action_items,
        'actionItemChecks': [False for _ in action_items],
        'sourceType': 'upload',
        'audioFileName': file.name,
    }
