from django.conf import settings
from .client import get_model, get_openai_client
from .prompts import MEETING_SUMMARY_PROMPT, STAR_PORTFOLIO_PROMPT, STAR_SUMMARY_PROMPT


def summarize_meeting_note(content: str) -> str:
    model = get_model()
    response = model.generate_content(
        MEETING_SUMMARY_PROMPT.format(content=content),
        request_options={'timeout': settings.GOOGLE_AI_TIMEOUT_SECONDS},
    )
    return response.text


def transcribe_audio_file(file) -> str:
    file.seek(0)
    model = settings.OPENAI_TRANSCRIPTION_MODEL
    request_kwargs = {
        'model': model,
        'file': (file.name, file, getattr(file, 'content_type', 'application/octet-stream')),
        'language': 'ko',
    }

    if model == 'whisper-1':
        request_kwargs['response_format'] = 'text'
    else:
        request_kwargs['response_format'] = 'json'

    transcription = get_openai_client().audio.transcriptions.create(
        **request_kwargs,
    )
    return getattr(transcription, 'text', str(transcription)).strip()


def generate_star_summary(situation: str, task: str, action: str, result: str) -> str:
    model = get_model()
    response = model.generate_content(
        STAR_SUMMARY_PROMPT.format(
            situation=situation,
            task=task,
            action=action,
            result=result,
        ),
        request_options={'timeout': settings.GOOGLE_AI_TIMEOUT_SECONDS},
    )
    return response.text


def generate_star_portfolio_draft(content: str) -> str:
    model = get_model()
    response = model.generate_content(
        STAR_PORTFOLIO_PROMPT.format(content=content),
        request_options={'timeout': settings.GOOGLE_AI_TIMEOUT_SECONDS},
    )
    return response.text
