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
- **적응기 · 1강** — [git-setup](00_onboarding/b_q_git-setup/) — 개발환경 세팅(Git·GitHub·SSH)
- **적응기 · 5강** — [computational-thinking](00_onboarding/d_hw_computational-thinking/) — 컴퓨팅 사고 프로젝트(분해·패턴·추상화·알고리즘)

### 모듈1 · 바이브코딩으로 웹페이지 만들기
- **노드7 · 메인 퀘스트** — [ORIGIN 소스](02_module1/a_mq_L7-origin/) · [라이브 ↗](https://kdt-origin.vercel.app) — 디자인 영감 아카이브(Next.js·Supabase·Claude API)
- **퀘스트** — [B 팀티칭](02_module1/b_q_B-git-teaching/) · [C1 틀린그림찾기](02_module1/b_q_C1-spot-the-difference/) · [C2 코드리뷰](02_module1/b_q_C2-code-review/)
- **실습** — [노드5 · 7강 todo-app](02_module1/c_lab_L5-todo-app/) · [노드6 · 6강 agent-practice](02_module1/c_lab_L6-agent-practice/)
- **과제** — [노드2 · 6강 soul-dungeon](02_module1/d_hw_L2-soul-dungeon/) · [노드4 · 9강 world-atlas](02_module1/d_hw_L4-world-atlas/) · [노드6 · 7강 agent-skills](02_module1/d_hw_L6-agent-skills/)

### 모듈2 · AI의 이해와 사용_Agt1
- **노드9 · 메인 퀘스트** — [명화의 주인공 되기](03_module2/a_mq_N9-art-face-fusion/) — 사람 사진을 명화에 합성(ControlNet + SAM)
- **퀘스트** — [A 트랜스포머 발표](03_module2/b_q_A-transformer-preso/) — 티처팀 통합 발표
- **과제** — [노드5 · 8강 원하는 포즈로 만들기](03_module2/d_hw_N5-pose-image-tool/) · [Colab에서 열기 ↗](https://colab.research.google.com/github/kimjy0977/KDT_Works/blob/main/03_module2/d_hw_N5-pose-image-tool/pose_tool.ipynb) · [노드7 폰 영상으로 3D 방](03_module2/d_hw_N7-room-3d/)

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
- **노드9 · 실습 프로젝트** — [딥리서처 — 세계 신화](05_module5/d_hw_N9-myth-research/) — 한 번에 못 읽는 위키 42건(34.9만자 = 모델 창의 **1.37배**)을 넷이 나눠 읽고 한 편으로 합친다. **정답표 없이** 채점하고 **혼자 하는 대조군과 예산을 맞춰** 붙였다. ★같은 설정 15회가 48.6~74.3%로 흩어져 **잡음(25.6%p)이 조건 차이(17.8%p)보다 크다** — 갈리는 것은 solo 뿐
- **노드8 · 실습** — [딥리서치 에이전트 — 코디네이터 + 서브에이전트](05_module5/c_lab_N8-deepresearch/) — 한국 근대사 위키 32건. 코디네이터가 목차를 짜고 서브에이전트 넷을 **동시에** 파견해 각자 한 절씩. 절제 실험으로 **무엇이 실제로 값을 하는지** 쟀다
- **노드7 · 실습 프로젝트** — [영화 딜레마 그래프 에이전트](05_module5/d_hw_N7-graph-agent/) — 물음·가치대립으로 그래프를 세워 「같은 딜레마를 다룬 영화」를 **4홉**으로 찾는다. 이름이 아니라 **축과 극**으로 합쳐 다리가 2→6개. 근거 없으면 **거절**. basic RAG 는 전 구간 0.0%
- **노드6 · 실습** — [시네필 위키 — 지식 그래프와 GraphRAG](05_module5/c_lab_N6-graphrag/) — 위키 영화 문서 80건 → 삼중항 2,103개. 지역·경로·전역 세 갈래 질의를 basic RAG 와 **같은 잣대로** 비교(단순 86.7% vs 추천 51.8%)
- **노드5 · 실습 프로젝트** — [발견 데스크 — 확실성을 말하는 과학 질문 에이전트](05_module5/d_hw_N5-discovery-desk/) — 확실성 등급(**[정설]·[추정]·[논쟁]·[신설]**)과 함께 답한다. 가드레일 3겹 · 홀드아웃 평가
- **노드4 · 실습** — [고객 응대 에이전트 — 라우팅과 그라운딩](05_module5/c_lab_N4-routing-grounding/) — OpenAI 키 없이 의도 분류·답변 두 지표를 측정. **규칙 라우터를 기준선으로** 세우고 LLM 과 견줌
- **노드3 · 프로젝트** — [「이번 주의 발견」 뉴스레터 에이전트](05_module5/d_hw_N3-newsletter/) — 우주·고고학·고생물 14소스 → 선별·요약·**3겹 검수** → Discord 발행(LangGraph · 키 없이 로컬 Ollama)

### 해커톤
- **기업연계 · 팀 《순순히 따라와라》** — [누가 내 케이크 먹었어?](90_hackathon/01_soonsoon-social-deduction/) — 셰어하우스 거주자 5명 중 범인을 찾는 **AI 소셜 추리 게임**. 주식회사 순순팩토리 기업연계 과제 (SPUM Engine · SAM LLM)

### 도메인개발 (백엔드 자가연습)
- [opening-trainer](99_domain-dev/opening-trainer/) · [정적 UI ↗](https://kimjy0977.github.io/KDT_Works/99_domain-dev/opening-trainer/static/) — 체스 오프닝 트레이너(FastAPI + JSON). 정적 UI는 공개, API는 로컬 실행.

---
*Made with vibe coding · KDT AI 에이전트 1기*
