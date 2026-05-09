import google.generativeai as genai
from django.conf import settings

_model = None
_openai_client = None


def get_model() -> genai.GenerativeModel:
    global _model
    if _model is None:
        genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
        _model = genai.GenerativeModel('gemini-1.5-flash')
    return _model


def get_openai_client():
    global _openai_client
    if not settings.OPENAI_API_KEY:
        raise ValueError('OPENAI_API_KEY가 설정되어 있지 않습니다.')
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client
