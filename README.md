# KDT_Works

> 갱신 2026-09-15 — **모듈3·4·5·해커톤이 통째로 빠져 있었다**(산출물 27개 중 13개 미언급).
> 초안 = 튜터 · 반영 = 매니저(§9-4 루트는 매니저 «그릇»).
> ⇒ 감사 도구 `갤러리-감사.py` 가 이제 **README 도 같이 센다** — 갤러리만 보던 구멍이었다.

아이펠 KDT AI 에이전트 1기 **작업물 아카이브** — 온보딩·모듈별 과제·실습·퀘스트.

## 🔗 바로가기
- **갤러리(허브):** https://kimjy0977.github.io/KDT_Works/
- **학습로그·가이드:** [강의노트(앤트로픽·인프런)](https://kimjy0977.github.io/KDT_Works/00_log/강의노트-앤트로픽.html) · [모두연 노드 강의노트](https://kimjy0977.github.io/KDT_Works/00_log/강의노트-모두연.html)

## 구조 (모듈 > 노드 > 강 · 접두사 정렬)
`a_mq` 메인퀘 · `b_q` 퀘스트 · `c_lab` 실습 · `d_hw` 과제

### 온보딩
- **적응기 · 1강** — [git-setup](01_onboarding/b_q_git-setup/) — 개발환경 세팅(Git·GitHub·SSH)
- **적응기 · 5강** — [computational-thinking](01_onboarding/d_hw_computational-thinking/) — 컴퓨팅 사고 프로젝트(분해·패턴·추상화·알고리즘)

### 모듈1 · 바이브코딩으로 웹페이지 만들기
- **노드7 · 메인 퀘스트** — [ORIGIN 소스](02_module1/a_mq_L7-origin/) · [라이브 ↗](https://kdt-origin.vercel.app) — 디자인 영감 아카이브(Next.js·Supabase·Claude API)
- **퀘스트** — [B 팀티칭](02_module1/b_q_B-git-teaching/) · [C1 틀린그림찾기](02_module1/b_q_C1-spot-the-difference/) · [C2 코드리뷰](02_module1/b_q_C2-code-review/)
- **실습** — [노드5 · 7강 todo-app](02_module1/c_lab_L5-todo-app/) · [노드6 · 6강 agent-practice](02_module1/c_lab_L6-agent-practice/)
- **과제** — [노드2 · 6강 soul-dungeon](02_module1/d_hw_L2-soul-dungeon/) · [노드4 · 9강 world-atlas](02_module1/d_hw_L4-world-atlas/) · [노드6 · 7강 agent-skills](02_module1/d_hw_L6-agent-skills/)

### 모듈2 · AI의 이해와 사용_Agt1
- **노드9 · 메인 퀘스트** — [명화의 주인공 되기](03_module2/a_mq_N9-art-face-fusion/) — 사람 사진을 명화에 합성(ControlNet + SAM)
- **퀘스트** — [A 트랜스포머 발표](03_module2/b_q_A-transformer-preso/) — 티처팀 통합 발표
- **과제** — [노드5 · 8강 원하는 포즈로 만들기](03_module2/d_hw_N5-pose-image-tool/) · [Colab에서 열기 ↗](https://colab.research.google.com/github/kimjy0977/KDT_Works/blob/main/03_module2/d_hw_N5-pose-image-tool/pose_tool.ipynb) · [노드7 폰 영상으로 3D 방](03_module2/d_hw_N6-room-3d/)

### 모듈3 · 프롬프트 엔지니어링
- **노드5 · 메인 퀘스트** — [MYTH GALLERY 안내 챗봇](04_module3/a_mq_N5-myth-rag-guide/) — RAG로 **근거를 걸고** 답하는 가이드 챗봇
- **퀘스트** — [B 평가지표 사전](04_module3/b_q_B-eval-metrics-teaching/) — 「답을 재는 방법」 팀 티칭
- **실습** — [노드1 프롬프트 층 바꾸기](04_module3/c_lab_N1-prompt-layers/) — 한 층만 바꿔 결과 차이 보기
- **과제** — [노드4 서비스 설계](04_module3/d_hw_N4-service-agent-design/) — 가이드 챗봇 서비스 설계

### 모듈4 · AI Agent 파헤치기
- **노드7 · 메인 퀘스트** — [CURATOR](05_module4/a_mq_N7-domain-agentic-workflow/) — 아카이브 등재 에이전트(사용자와 함께 만드는 카드뉴스)
- **프로젝트** — [노드6 나만의 에이전트 하네스](05_module4/a_mq_N6-agent-harness/) — 하네스를 직접 설계·제작
- **실습** — [노드1 n8n → 내 Ollama 터널](05_module4/c_lab_N1-ollama-tunnel/) · [노드7 카드뉴스 1~5강](05_module4/c_lab_N7-cardnews/)
- **과제** — [노드2 하네스 비교 실험](05_module4/d_hw_N2-agent-harness-experiment/) — 「저장소 구조를 먼저 주면 «없다»는 오답이 줄어드는가」 가설 검증(2차 6시행, 가설 기각)

### 모듈5 · 에이전트 팀 꾸리기
- **노드3 · 프로젝트** — [「이번 주의 발견」 뉴스레터 에이전트](05_module5/d_hw_N3-newsletter/) — 우주·고고학·고생물 14소스 → 선별·요약·**3겹 검수** → Discord 발행(LangGraph · 키 없이 로컬 Ollama)

### 해커톤
- [순순팩토리](90_hackathon/) — 팀 프로젝트

### 도메인개발 (백엔드 자가연습)
- [opening-trainer](99_domain-dev/opening-trainer/) · [정적 UI ↗](https://kimjy0977.github.io/KDT_Works/99_domain-dev/opening-trainer/static/) — 체스 오프닝 트레이너(FastAPI + JSON). 정적 UI는 공개, API는 로컬 실행.

---
*Made with vibe coding · KDT AI 에이전트 1기*
