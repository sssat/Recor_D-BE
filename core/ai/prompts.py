MEETING_SUMMARY_PROMPT = """다음 회의록을 분석하여 아래 형식으로 요약해주세요.

**주요 결정 사항**
- (결정된 내용을 간결하게 나열)

**액션 아이템**
- (담당자: 할 일)

**다음 회의 안건**
- (논의할 내용)

회의록:
{content}"""

STAR_SUMMARY_PROMPT = """다음 프로젝트 경험을 STAR 기법을 바탕으로 포트폴리오용 소개글로 작성해주세요.
자연스러운 한 문단으로 200자 내외로 작성하고, 수치나 성과가 있으면 반드시 포함하세요.

상황(Situation): {situation}
목표(Task): {task}
행동(Action): {action}
결과(Result): {result}"""

STAR_PORTFOLIO_PROMPT = """다음 프로젝트 기록을 분석해서 취업 포트폴리오에 바로 넣을 수 있는 STAR 초안을 작성해주세요.
반드시 JSON 객체 하나만 응답하고, 마크다운 코드블록은 사용하지 마세요.

필드:
- title: 포트폴리오 제목
- summary: 120자 이내 요약
- keywords: 핵심 키워드 문자열 배열 3~6개
- situation: 프로젝트 배경과 문제 상황
- task: 내가 맡은 역할과 해결해야 했던 과제
- action: 구체적인 행동 문자열 배열 3~5개
- result: 결과와 배운 점, 가능하면 수치 포함

프로젝트 기록:
{content}"""
