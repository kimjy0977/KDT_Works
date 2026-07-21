# 퀘스트 C-2 · 코드 피어리뷰

> 노션 퀘스트 C-2. 파트너의 제출물을 코드 리뷰하고, PR로 피드백을 제출하는 상호 피어리뷰.
> 리뷰어: 김주영 · 파트너: SunCreation

## 내가 리뷰어로서 한 것
- 대상: **SunCreation/realtodo** (macOS SwiftUI + GRDB/SQLite + Google Calendar + AI CLI 투두 앱)
- AIFFEL PRT 5문항 + 프로젝트 제출 루브릭(보안 / 백엔드 / 프론트) 기준으로 근거를 채워 리뷰
- fork에 `review.md` 커밋 → **PR 제출**: https://github.com/SunCreation/realtodo/pull/1
- 주요 발견: 아침 AI 루틴 타이머 일회성 버그(핵심 워크플로 정지) · OAuth state/PKCE 부재(CSRF) · 토큰 평문 저장 · 회고 부재
- 칭찬: AI CRUD를 자기 추천 id로만 한정한 방어 설계(무결성)
- ※ macOS 전용이라 리뷰어(Windows)는 빌드·실행 미검증 — 코드 판독 기반임을 명시

## 리뷰 본문
→ [`review.md`](./review.md)

## 내가 코더로서 받은 것
- 파트너가 내 `node4-world-atlas` 백엔드를 리뷰해 PR로 보냄 → 소스 대조로 검증(전부 사실) → **병합**
- 수용한 개선: `code` 형식 CHECK(저장소 고갈 방어) 등 보안 하드닝을 라이브 DB에 적용
