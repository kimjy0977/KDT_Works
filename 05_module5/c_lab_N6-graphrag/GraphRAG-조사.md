# GraphRAG 조사 — 4주제

**왜 쓰나** 노션 「오늘 학습 방식」이 **서칭으로 4주제를 조사**하고 **팀별로 공유**하라고 지시.
**언제** 2026-09-18 · **무엇으로** 노드가 지정한 1차 자료 + 웹 검색
✅ 폴더 이름의 **`N6` 은 확인됐다** — LMS 커리큘럼 제목이 **「6.영화 추천 에이전트 만들기 - GraphRAG」**
(2026-09-18 13:0x 실측). 총 **16강**이고 배너 「에이전트 팀 꾸리기_Agt1」은 **LMS 패키징**일 뿐이다.

---

## 0. 한 장 요약 — 팀에 이 순서로 말하면 된다

```
① 벡터 RAG 는 «비슷한 것»을 찾는다.   → 「이어 붙여야 나오는 답」을 못 만든다
② 그래서 사실을 «점과 선»으로 미리 적어 둔다 (지식 그래프)
③ 그런데 점·선을 «아무렇게나» 뽑으면 쓸모없다 → 무엇을 뽑을지 정하는 규칙 = 온톨로지
④ 이걸 검색에 붙인 것이 GraphRAG. 비용은 «질문할 때»가 아니라 «넣을 때» 든다
```

★**오늘 노드의 한 줄과 같은 말이다** —
*「벡터 RAG는 «질문이 들어온 뒤에» 연결을 만들려 하기 때문에 멀티홉에서 실패합니다.
GraphRAG는 «문서를 넣는 시점에» 미리 연결을 만들어 두죠.」*

---

## 1. Basic RAG 의 한계점과 발전된 기법

### 한계 — 마이크로소프트가 든 실제 사례

> *"Baseline RAG **struggles to connect the dots**. This happens when answering a question
> requires traversing disparate pieces of information through their shared attributes"*
> — MS Research 블로그

**실제로 이렇게 실패했다.** 「What has Novorossiya done?」를 물었더니
*"The text does not provide specific information on what Novorossiya has done"* 라고 답했다.
**자료에는 있었다.** 벡터 검색이 못 데려온 것이다.

한계는 둘로 갈린다.

| 무엇을 못 하나 | 왜 |
|---|---|
| **이어 붙이기(멀티홉)** | 답이 한 문서에 없다. 두 문서를 걸쳐야 나온다 |
| **전체를 훑는 질문** | *"이 자료 전체의 주제가 뭐야?"* — 이건 «검색»이 아니라 «요약»이다 |

> *"RAG **fails on global questions** directed at an entire text corpus,
> such as 'What are the main themes in the dataset?'"* — GraphRAG 원논문 초록

### 발전된 기법 — GraphRAG 말고도 여럿

| 기법 | 한 줄 |
|---|---|
| **Hybrid Search** | 키워드 색인 + 벡터 색인을 **둘 다** 만들어 함께 검색 |
| **Reranking** | 일단 많이 가져온 뒤 **다시 줄 세운다** (cross-encoder 또는 LLM) |
| **HyDE** | 질문 대신 **«가상의 답»을 만들어 그걸로 검색.** 질문과 답은 임베딩 공간에서 모양이 달라서 |
| **Self-RAG** | 가져온 문서를 **스스로 평가해** 쓸모없으면 버리고 다시 가져온다 |
| **CRAG** | 근거가 약하면 **답하기 전에** 걸러낸다 |
| **GraphRAG** | ★애초에 **관계를 미리 만들어 둔다** |

⚠ **수치 하나** — 2024 벤치마크에서 최신 RAG 시스템도 사실 질문의 **63%**만 맞혔다.
아무 기법 없는 단순 검색은 **44%**. (기법을 쌓아도 천장이 있다는 뜻)

★**앞의 다섯은 「질문이 온 뒤에 더 잘 찾는」 방법이고, GraphRAG 하나만 「미리 만들어 두는」 방법이다.**
이 구분이 오늘 노드의 핵심이다.

---

## 2. 온톨로지와 지식 그래프의 도입 이유

### 지식 그래프 = 사실을 점과 선으로

```
(봉준호, DIRECTED, 기생충)     ← 삼중항 하나
(송강호, ACTED_IN, 기생충)

⇒ 이어 붙이면 "봉준호 영화에 나온 배우는?" 의 답이 된다
```

따로 보면 평범한 사실인데 **이어 붙이면 새 답**이 된다. 문서로는 못 하는 일이다.

### 그런데 왜 «온톨로지»까지 필요한가

**자동으로 만든 지식 그래프는 잘 안 쓰인다.** 이유가 명확하다.

> 자동 구축된 지식 그래프는 **명시적 개념 구조가 없고**, 대부분의 노드가
> **일반적이고 표면적인 이름**으로 붙는다 — 특히 비정형 텍스트에서 만든 경우.

⇒ 온톨로지는 **「무엇을 점으로 삼고 무엇을 선으로 삼을지」 정한 규칙**이다.
사실만이 아니라 **의미·계층·맥락**을 담는다.

**모호성 해소(disambiguation) 예시** — 「정책」을 물었을 때

```
단순 RAG    서로 다른 종류의 정책 조각이 뒤섞여 나온다
온톨로지    정책 «종류»를 구분해 각각 다른 관계로 표현해 둔다
```

★**오늘 노드가 이걸 정확히 시킨다** —
*「텍스트에서 LLM으로 관계를 뽑되, **답해야 할 질문에서 스키마를 역산해**
무엇을 뽑을지 먼저 좁힙니다.」*
= 온톨로지를 먼저 정하는 일이다. 노드는 그 말을 안 쓰고 「스키마」라고 부를 뿐이다.

---

## 3. GraphRAG 의 특징과 장점

### 파이프라인 (MS 블로그 기준)

```
1  LLM 이 전체 데이터셋을 훑어 «모든 엔티티와 관계»를 뽑아 지식 그래프를 만든다
2  그래프를 «하향식 클러스터링» 해서 의미 덩어리(커뮤니티)로 계층화한다
3  질문이 오면 «둘 다» 써서 LLM 문맥창을 채운다
```

원논문은 3단계를 이렇게 적는다 — ①엔티티 지식 그래프 도출 → ②**밀접한 엔티티 그룹별
커뮤니티 요약을 미리 생성** → ③각 커뮤니티 요약으로 부분 응답을 만든 뒤 최종 요약.

### 장점

| | |
|---|---|
| **멀티홉을 푼다** | 관계가 이미 그려져 있으니 따라 걸으면 된다 |
| **전역 질문에 답한다** | 커뮤니티 요약을 **미리** 만들어 두어서 |
| **★출처를 댄다** | *"GraphRAG provides the **provenance**, or source grounding information, as it generates each response"* |
| **검색 품질 자체가 오른다** | *"vastly improves the '**retrieval**' portion of RAG, populating the context window with higher relevance content"* |

### ⚠ 정직하게 — 「무조건 좋다」가 아니다

- MS 블로그의 비교는 **정량 수치가 없다.** LLM 평가자의 **쌍별 비교**로
  *"consistently outperforms"* 라고만 했다. 지표는 **포괄성·다양성** 등
- **충실성(faithfulness)** 은 SelfCheckGPT 측정에서 **baseline RAG 와 비슷**했다
  → 즉 **「덜 지어낸다」는 근거는 약하다.** 더 넓고 다양하게 답한다는 쪽이다
- 원논문 초록에도 *"substantial improvements ... for both the **comprehensiveness and diversity**"* 로
  **두 축만** 적혀 있다
- ★**비용이 앞으로 옮겨 갈 뿐 사라지지 않는다.** 노드가 직접 경고한다 —
  *「오늘 쓰는 토큰의 **8할 이상**이 그 한 섹션에서 나간다」* (그래프 만드는 섹션)

---

## 4. GraphRAG 도입 사례

| 사례 | 규모·결과 |
|---|---|
| **도매 유통사** (Neo4j 기반) | 데이터 소스 **14개** 통합 · 그래프가 **노드 1,200만 · 관계 8,900만** 으로 성장.<br>고객→주문→상품→부품→공급사 를 이어 모델링 |
| **레거시 코드 마이그레이션** (SAP · arXiv 2507.03226) | 순수 벡터 검색 대비 **최대 15% · 4.35%** 개선 (LLM-as-Judge 평가) |
| **하이브리드 아키텍처** 사례 | 그래프 순회 + 벡터 유사도를 **함께** — PostgreSQL · Neo4j · Milvus · Debezium CDC 조합 |

★**공통점** — 전부 *"엔티티 사이의 관계를 따라가야 답이 나오는"* 업무다.
고객·주문·상품·공급사처럼 **연결이 곧 의미인** 자료에서 벡터 검색이 먼저 무너진다.

⚠ **한계도 같이 봐야 한다** — 1,200만 노드를 만들려면 그만큼 LLM 을 돌려야 한다.
「개선 15%」를 얻는 비용이 얼마였는지는 이 자료들에 안 적혀 있다.

---

## 5. ★우리 노드5 프로젝트와 겹치는 것 (팀 공유 때 꺼낼 거리)

오늘 노드가 쓰는 방법이 **우리가 이미 한 것과 같다.**

```
기준선을 «먼저» 잡는다      노드5: 규칙 라우터   /  오늘: BM25
같은 잣대로 전후 비교         노드5: 골든셋 25건  /  오늘: 골든셋 15문항
실패를 «원인별로» 가른다      노드5: 분류·근거    /  오늘: 색인·검색·생성
★천장까지 안 올린다          노드5 REPORT 와 «같은 문장» —
                            「무엇이 부족한지 숫자로 말할 수 있게 되는 것」
```

**질문거리로 좋은 것**
- 온톨로지를 «먼저» 정하면 **그 스키마 밖의 사실은 영영 안 들어온다.** 이 손실은 어떻게 보나?
- GraphRAG 의 충실성이 baseline 과 비슷하다면, **「지어내기」를 줄이려는 목적**으로는 왜 부족한가?
- 비용이 색인 시점으로 옮겨 가면 **자료가 자주 바뀌는 도메인**에서는 어떻게 되나?
  (노드5 에서 우리가 겪은 것 — 지식원이 72시간마다 갱신됐다)

---

## 출처

- [GraphRAG: Unlocking LLM discovery on narrative private data](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/) — MS Research 블로그
- [From Local to Global: A Graph RAG Approach to Query-Focused Summarization](https://arxiv.org/abs/2404.16130) — arXiv 2404.16130 (Edge, Trinh, Cheng, Bradley, Chao, Mody, Truitt, Metropolitansky, Ness, Larson)
- [Microsoft GraphRAG 공식 문서](https://microsoft.github.io/graphrag/)
- [How to construct knowledge graphs](https://python.langchain.com/docs/how_to/graph_constructing/) — LangChain
- [Ontology-Driven Knowledge Graph for GraphRAG](https://deepsense.ai/resource/ontology-driven-knowledge-graph-for-graphrag/) — deepsense.ai
- [From RAG to GraphRAG: Knowledge Graphs, Ontologies and Smarter AI](https://www.gooddata.ai/blog/from-rag-to-graphrag-knowledge-graphs-ontologies-and-smarter-ai/) — GoodData
- [Enhancing GraphRAG Using LLM Generated Ontology from Text](https://link.springer.com/chapter/10.1007/978-3-032-29003-8_25) — Springer
- [12 Advanced RAG Techniques: Beyond Naive Retrieval](https://atlan.com/know/advanced-rag-techniques/) — Atlan
- [Advanced RAG techniques for high-performance LLM applications](https://neo4j.com/blog/genai/advanced-rag-techniques/) — Neo4j
- [GraphRAG Implementation: What 12 Million Nodes Taught Us](https://particula.tech/blog/graphrag-implementation-enterprise-data-platform) — Particula
- [arXiv 2507.03226](https://arxiv.org/html/2507.03226v3) — SAP, 레거시 코드 마이그레이션 사례
