# Recor-D Backend

프로젝트, 일정, 할 일, 회의록, 포트폴리오 작성을 지원하는 Recor-D 서비스의 백엔드 API입니다.

## 주요 기능

- 카카오 소셜 로그인
- JWT 기반 인증
- 대시보드 요약 API
- 프로젝트, 할 일, 일정 관리 API
- 회의록 작성, 조회, 수정, 삭제 API
- 녹음 파일 업로드 기반 회의록 초안 생성
- OpenAI 음성 인식 API 연동
- Google Gemini 기반 회의록 요약 생성
- 포트폴리오 초안 및 STAR 형식 요약 생성
- Swagger API 문서 제공

## 기술 스택

- Python
- Django 4.2
- Django REST Framework
- PostgreSQL
- Simple JWT
- django-cors-headers
- drf-spectacular
- OpenAI API
- Google Generative AI

## 실행 방법

### 1. 의존성 설치

```powershell
python -m pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env.example`을 복사해 `.env` 파일을 만듭니다.

```powershell
Copy-Item .env.example .env
```

이후 `.env`에 로컬 DB 정보, 카카오 REST API 키, OpenAI API 키, Google AI API 키를 입력합니다.

### 3. PostgreSQL 실행

Docker를 사용하는 로컬 실행 예시는 다음과 같습니다.

```powershell
docker run --name record-postgres `
  -e POSTGRES_DB=record_db `
  -e POSTGRES_USER=record_user `
  -e POSTGRES_PASSWORD=record_password `
  -p 5432:5432 `
  -d postgres:16
```

위 설정을 사용할 경우 `DATABASE_URL`은 다음과 같습니다.

```env
DATABASE_URL=postgres://record_user:record_password@localhost:5432/record_db
```

### 4. 마이그레이션 실행

```powershell
python manage.py migrate
```

### 5. 개발 서버 실행

```powershell
python manage.py runserver 127.0.0.1:8000
```

API 서버는 아래 주소에서 실행됩니다.

```text
http://localhost:8000
```

## 환경변수

로컬 개발 기준 `.env` 예시는 다음과 같습니다.

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgres://record_user:record_password@localhost:5432/record_db
ALLOWED_HOSTS=localhost,127.0.0.1

GOOGLE_AI_API_KEY=your-google-ai-api-key
GOOGLE_AI_MODEL=gemini-2.5-flash
GOOGLE_AI_TIMEOUT_SECONDS=60

OPENAI_API_KEY=your-openai-api-key
OPENAI_TRANSCRIPTION_MODEL=gpt-4o-transcribe
OPENAI_TIMEOUT_SECONDS=90

KAKAO_REST_API_KEY=your-kakao-rest-api-key
KAKAO_CLIENT_SECRET=
KAKAO_REDIRECT_URI=http://localhost:3000/oauth/callback/kakao

CORS_ALLOWED_ORIGINS=http://localhost:3000
```

## 카카오 로그인 설정

Kakao Developers에서 다음 값을 설정합니다.

- 플랫폼: Web
- 사이트 도메인: `http://localhost:3000`
- Redirect URI: `http://localhost:3000/oauth/callback/kakao`
- 카카오 로그인: 활성화
- 클라이언트 시크릿: 백엔드에서 사용하지 않으면 비활성화
- 동의항목: 닉네임

## API 문서

개발 서버 실행 후 아래 주소에서 Swagger 문서를 확인할 수 있습니다.

```text
http://localhost:8000/api/docs/
```

OpenAPI 스키마는 아래 주소에서 확인할 수 있습니다.

```text
http://localhost:8000/api/schema/
```

## 주요 명령어

```powershell
python manage.py check
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

## ERD

- [ERD Cloud](https://www.erdcloud.com/d/E23uQY3p3nFSTBz9H)

## 주의사항

- 실제 키가 들어 있는 `.env` 파일은 커밋하지 않습니다.
- 공유용 환경변수 형식은 `.env.example`에만 작성합니다.
- `.env`를 수정한 뒤에는 백엔드 서버를 재시작해야 합니다.
- 로컬에서 실행할 때는 PostgreSQL 컨테이너가 먼저 실행 중이어야 합니다.
