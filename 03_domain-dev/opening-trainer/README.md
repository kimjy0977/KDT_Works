# ♟️ Opening Trainer (오프닝 훈련 앱)

체스 오프닝을 **선택해서 AI와 수를 연습·학습**하는 앱. (KDT 도메인 개발 프로젝트)

## 오늘(1일차) 목표 — 데이터 척추
오프닝을 저장·조회하는 백엔드 API from scratch.

- **M1** 서버 뜨고 `GET /health` 200 ✅ 목표
- **M2** `POST /openings` 저장 + `GET /openings`·`GET /openings/{id}`
- **M3** 최소 폼 등록→목록/상세 + push

## 실행법
```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
→ http://127.0.0.1:8000/health · 자동 문서 http://127.0.0.1:8000/docs

## 스택
FastAPI + JSON 파일 저장. (다음 모듈에 SQLite·수 검증·AI 코치로 확장)
