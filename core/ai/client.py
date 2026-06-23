import google.generativeai as genai
from django.conf import settings

_model = None
_openai_client = None


def get_model() -> genai.GenerativeModel:
    global _model
    if _model is None:
        genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
        _model = genai.GenerativeModel(settings.GOOGLE_AI_MODEL)
    return _model


def get_openai_client():
    global _openai_client
    if not settings.OPENAI_API_KEY:
        raise ValueError('OPENAI_API_KEY is not configured.')
    if _openai_client is None:
        import httpx
        from openai import OpenAI

        _openai_client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
            http_client=httpx.Client(
                trust_env=False,
                timeout=settings.OPENAI_TIMEOUT_SECONDS,
            ),
        )
    return _openai_client
