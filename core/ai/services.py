from django.conf import settings
from .client import get_model, get_openai_client
from .prompts import MEETING_SUMMARY_PROMPT, STAR_SUMMARY_PROMPT


def summarize_meeting_note(content: str) -> str:
    model = get_model()
    response = model.generate_content(MEETING_SUMMARY_PROMPT.format(content=content))
    return response.text


def transcribe_audio_file(file) -> str:
    file.seek(0)
    transcription = get_openai_client().audio.transcriptions.create(
        model=settings.OPENAI_TRANSCRIPTION_MODEL,
        file=(file.name, file, getattr(file, 'content_type', 'application/octet-stream')),
        response_format='text',
        language='ko',
    )
    return str(transcription).strip()


def generate_star_summary(situation: str, task: str, action: str, result: str) -> str:
    model = get_model()
    response = model.generate_content(
        STAR_SUMMARY_PROMPT.format(
            situation=situation,
            task=task,
            action=action,
            result=result,
        )
    )
    return response.text
