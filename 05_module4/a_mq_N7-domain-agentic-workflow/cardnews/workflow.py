# -*- coding: utf-8 -*-
"""카드뉴스 워크플로 — 조사 → 선택 → 심층검증 → 스토리보드 → 제작 → 검수.

★사람이 «중간에 끼어드는» 지점이 셋이다. 그 앞에서는 다음 단계로 넘어가지 않는다.
  ① 후보 선택   ② (필요하면) 독자 질문   ③ 스토리보드 승인

★엔진 호출은 «비싸다»(호출당 캐시 47K). 그래서 한 번에 최대한 받아 온다.
"""
import datetime
import json
import re
import threading
import time

import engine
import store

# 오래 걸리는 작업은 스레드로 돌리고 상태는 «파일»에 남긴다 — 서버가 죽어도 기록이 남게.
_RUNNING = {}


def _now_kst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))


def _period(days):
    end = _now_kst()
    start = end - datetime.timedelta(days=days)
    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d %H:%M %Z')


# ════════════════════════════════════════════════════════════
# ① 넓은 조사
# ════════════════════════════════════════════════════════════
RESEARCH_PROMPT = """당신은 카드뉴스 제작을 돕는 조사자입니다.

주제: {topic}
조사 기간: {start} ~ {end} (실행 시각 {now} 기준 최근 {days}일)

웹 검색으로 이 기간 안에 «실제로 게시된» 소식을 찾아 주세요.

## 반드시 지킬 것
1. **서로 다른 후보 7~12개.** 같은 발표를 다룬 기사는 «하나로 묶습니다».
2. 모델·제품·연구·개발도구 등 **종류가 다양하게** 섞이도록 고릅니다.
3. **최근에 «작성된» 소개 글이라고 «오래된 발표»를 새 소식으로 넣지 마세요.**
4. 날짜를 확인하지 못했으면 published 를 null 로 두고 uncertainty 에 적습니다.
5. 기간 안에 찾은 것이 부족하면 **찾은 만큼만** 주고 shortfall 에 실제 개수를 적습니다.

## 출력 — JSON 객체 하나만. 설명·코드펜스 없이.
{{"status":"result",
  "found": 실제로 찾은 개수,
  "shortfall": "부족하면 이유, 충분하면 null",
  "candidates":[
    {{"id":"c1","title":"제목","summary":"두 문장 요약",
      "published":"YYYY-MM-DD 또는 null","eventDate":"발표일 또는 null",
      "url":"원문 링크","kind":"모델|제품|연구|개발도구|정책|기타",
      "value":"이걸 고를 만한 이유 한 줄","uncertainty":"확인 못 한 것 한 줄"}}
  ]}}"""


def run_research(pid, widen=False):
    def work():
        st = store.load(pid)
        days = 30 if widen else st['periodDays']
        start, end, now = _period(days)
        prompt = RESEARCH_PROMPT.format(topic=st['topic'], start=start, end=end, now=now, days=days)

        store.update(pid, lambda s: (s.update({'status': 'researching', 'stage': 'research',
                                               'periodDays': days, 'searchedAt': now}),
                                     store.add_run(s, 'engine', step='research', note='웹 검색 시작')))
        r = engine.ask(prompt, session_id=st.get('sessionId'), cwd=store.engine_dir(pid),
                       tools=['WebSearch', 'WebFetch'], timeout=420)

        def apply(s):
            store.add_run(s, 'engine', step='research', ok=r['ok'], ms=r.get('ms'),
                          webSearches=r.get('webSearches'), costUsd=r.get('costUsd'),
                          reason=r.get('reason'))
            if not r['ok']:
                s['status'] = 'error'
                store.add_error(s, 'research', r['reason'], r.get('detail'),
                                retry='다시 조사하기 버튼을 누르세요')
                return
            if r.get('sessionId'):
                s['sessionId'] = r['sessionId']
            norm = engine.normalize(engine.extract_json(r['text']))
            if norm['kind'] == 'error':
                s['status'] = 'error'
                store.add_error(s, 'research', 'unparsable',
                                (r['text'] or '')[:400], retry='다시 조사하기')
                return
            data = norm.get('data') or {}
            cands = data.get('candidates') if isinstance(data, dict) else data
            cands = cands or []
            for i, c in enumerate(cands):
                c.setdefault('id', 'c%d' % (i + 1))
                if not c.get('published'):
                    c['published'] = None
                    c['uncertainty'] = (c.get('uncertainty') or '') + ' (게시일 미확인)'
            s['candidates'] = cands
            s['shortfall'] = data.get('shortfall') if isinstance(data, dict) else None
            s['status'] = 'ready'
            s['stage'] = 'select'
        store.update(pid, apply)
        _RUNNING.pop(pid, None)

    return _spawn(pid, 'research', work)


# ════════════════════════════════════════════════════════════
# ③ 심층 검증 + 편집 판단 (독자 질문이 여기서 나온다)
# ════════════════════════════════════════════════════════════
DEEP_PROMPT = """당신은 카드뉴스 제작을 돕는 편집자입니다.

사용자가 다음 소식을 골랐습니다:
{picked}

## 1단계 — 심층 검증
각 소식의 **공식 발표·제품 문서·변경 기록**을 웹에서 확인하세요.
- **확인한 사실** / **발표 주체의 주장** / **아직 확인 못 한 것** 을 «나눠서» 적습니다.
- 무엇이 달라졌는지 · 누가 «언제부터» 쓸 수 있는지 · 지역·계정·요금제 «조건»
- **공개 «예정»인 것을 «출시된 것»으로 바꾸지 마세요.**
- 자료끼리 날짜·조건이 어긋나면 conflicts 에 적습니다.

## 2단계 — 편집 판단
검증 결과를 바탕으로 **대상 독자**와 **카드 형식**을 정하고 이유를 답니다.
{audience_hint}

## 출력 — JSON 객체 하나만.
{{"status":"{want}",
  "research":{{
    "verified":["원문으로 확인한 사실"],
    "claims":["발표 주체의 주장"],
    "unverified":["확인 못 한 것"],
    "conflicts":["자료끼리 어긋나는 것"],
    "sources":[{{"title":"","url":"","published":""}}]
  }},
  "editorial":{{
    "audience":"정한 독자","why":"그렇게 본 이유 한 줄",
    "format":"목록형|단계 안내형|이야기형|비교형|체크리스트형",
    "formatWhy":"그 형식을 고른 이유",
    "hooks":["표지 문구 후보 2~3개"]
  }}{extra}}}"""

ASK_BLOCK = """,
  "question_id":"audience-1","version":1,
  "question":"어떤 독자에게 전달할까요?",
  "options":["AI 입문자","업무에 AI를 쓰는 사람","개발자"],
  "why":"선택에 따라 카드 순서와 설명 깊이가 크게 달라집니다\""""


def run_deep(pid):
    def work():
        st = store.load(pid)
        picked = [c for c in st['candidates'] if c['id'] in st['selection']]
        answered = {a['questionId'].split('-')[0] for a in st['answers']}
        # ★이미 답한 것은 다시 묻지 않는다 (PRD·3강)
        want_ask = 'audience' not in answered
        hint = ('독자가 이미 정해졌습니다: «%s». 다시 묻지 말고 그대로 쓰세요.'
                % _answer_of(st, 'audience')) if not want_ask else \
               ('독자에 따라 결과가 «크게» 달라지면 status 를 need_input 으로 하고 질문을 넣으세요. '
                '이미 명확하면 status 를 result 로 하고 추천 이유만 제시하세요.')
        prompt = DEEP_PROMPT.format(
            picked=json.dumps(picked, ensure_ascii=False, indent=1),
            audience_hint=hint,
            want='result' if not want_ask else 'result 또는 need_input',
            extra=ASK_BLOCK if want_ask else '')

        store.update(pid, lambda s: (s.update({'status': 'researching', 'stage': 'deep'}),
                                     store.add_run(s, 'engine', step='deep', note='심층 검증 시작')))
        r = engine.ask(prompt, session_id=st.get('sessionId'), cwd=store.engine_dir(pid),
                       tools=['WebSearch', 'WebFetch'], timeout=420)

        def apply(s):
            store.add_run(s, 'engine', step='deep', ok=r['ok'], ms=r.get('ms'),
                          webSearches=r.get('webSearches'), costUsd=r.get('costUsd'),
                          reason=r.get('reason'))
            if not r['ok']:
                s['status'] = 'error'
                store.add_error(s, 'deep', r['reason'], r.get('detail'), retry='심층 검증 다시')
                return
            if r.get('sessionId'):
                s['sessionId'] = r['sessionId']
            norm = engine.normalize(engine.extract_json(r['text']))
            if norm['kind'] == 'error':
                s['status'] = 'error'
                store.add_error(s, 'deep', 'unparsable', (r['text'] or '')[:400], retry='심층 검증 다시')
                return
            data = norm.get('data') or {}
            if isinstance(data, dict):
                s['research'] = data.get('research')
                s['editorial'] = data.get('editorial')
            if norm['kind'] == 'need_input':
                q = norm['question']
                q['version'] = 1
                s['question'] = q
                # ★질문을 기다리는 것은 «실패가 아니다». 완료로 표시하지 않는다.
                s['status'] = 'waiting_for_user'
                s['stage'] = 'deep'
            else:
                s['question'] = None
                s['status'] = 'ready'
                s['stage'] = 'storyboard'
        store.update(pid, apply)
        _RUNNING.pop(pid, None)

    return _spawn(pid, 'deep', work)


def _answer_of(st, prefix):
    for a in reversed(st['answers']):
        if a['questionId'].startswith(prefix):
            return a['answer']
    return None


# ════════════════════════════════════════════════════════════
# ④ 스토리보드
# ════════════════════════════════════════════════════════════
STORY_PROMPT = """검증한 내용으로 카드뉴스 스토리보드를 만드세요.

독자: {audience}
형식: {fmt}
카드 수: {n}장

## 반드시 지킬 것
- **한 장에 «메시지 하나».** 모든 장에 같은 정보를 반복하지 마세요.
- 표지는 관심을 끌되 **확인한 사실의 범위 안에서만** 씁니다. 근거 없는 순위·수치·과장 금지.
- 마지막 장은 **요약 또는 다음 행동**.
- 공개 «예정»인 기능이면 제목과 본문에 **예정임을 남깁니다**.
- imagePlan 은 «그림으로 설명할 수 있는» 장면이어야 합니다. 추상적 지시 금지.
- **그림에 글자를 넣으라고 하지 마세요.** 글자는 앱이 따로 얹습니다.

## 출력 — JSON 객체 하나만.
{{"status":"result","storyboard":{{
  "title":"카드뉴스 제목",
  "cards":[{{"n":1,"role":"표지|본문|요약","title":"카드 제목(20자 이내)",
             "body":"핵심 문장 1~2개(80자 이내)","source":"근거 URL",
             "imagePlan":"어떤 장면을 그릴지","imageQuery":"이미지 검색어(영문)"}}]
}}}}"""


def run_storyboard(pid, n_cards=5):
    def work():
        st = store.load(pid)
        ed = st.get('editorial') or {}
        aud = _answer_of(st, 'audience') or ed.get('audience') or '일반 독자'
        prompt = STORY_PROMPT.format(audience=aud, fmt=ed.get('format') or '목록형', n=n_cards)
        store.update(pid, lambda s: (s.update({'status': 'researching', 'stage': 'storyboard'}),
                                     store.add_run(s, 'engine', step='storyboard', note='기획 시작')))
        r = engine.ask(prompt, session_id=st.get('sessionId'), cwd=store.engine_dir(pid), timeout=300)

        def apply(s):
            store.add_run(s, 'engine', step='storyboard', ok=r['ok'], ms=r.get('ms'),
                          costUsd=r.get('costUsd'), reason=r.get('reason'))
            if not r['ok']:
                s['status'] = 'error'
                store.add_error(s, 'storyboard', r['reason'], r.get('detail'), retry='기획 다시')
                return
            if r.get('sessionId'):
                s['sessionId'] = r['sessionId']
            data = (engine.normalize(engine.extract_json(r['text'])).get('data') or {})
            sb = data.get('storyboard') if isinstance(data, dict) else None
            if not sb or not sb.get('cards'):
                s['status'] = 'error'
                store.add_error(s, 'storyboard', 'empty', (r['text'] or '')[:400], retry='기획 다시')
                return
            prev = (s.get('storyboard') or {}).get('version', 0)
            sb['version'] = prev + 1
            sb['approved'] = False
            s['storyboard'] = sb
            s['status'] = 'ready'
            s['stage'] = 'storyboard'
        store.update(pid, apply)
        _RUNNING.pop(pid, None)

    return _spawn(pid, 'storyboard', work)


# ════════════════════════════════════════════════════════════
def _spawn(pid, kind, work):
    if _RUNNING.get(pid):
        return {'ok': False, 'reason': 'already_running', 'detail': '이미 작업이 돌고 있습니다'}
    run_id = store.new_id('run')
    _RUNNING[pid] = run_id

    def guarded():
        try:
            work()
        except Exception as e:
            import traceback
            store.update(pid, lambda s: (s.update({'status': 'error'}),
                                         store.add_error(s, kind, 'crashed',
                                                         traceback.format_exc()[-600:],
                                                         retry='다시 시도')))
            _RUNNING.pop(pid, None)
    threading.Thread(target=guarded, daemon=True).start()
    return {'ok': True, 'runId': run_id, 'status': 'running'}


def is_running(pid):
    return _RUNNING.get(pid)


def recover(pid):
    """★서버 재시작 뒤 «중단된 작업»을 알아본다.

    메모리의 스레드는 사라졌지만 파일의 상태는 남아 있다.
    researching 인 채 멈춰 있으면 «완료로 위장하지 않고» 중단으로 표시한다.
    """
    st = store.load(pid)
    if st and st['status'] == 'researching' and not _RUNNING.get(pid):
        def apply(s):
            s['status'] = 'error'
            store.add_error(s, s.get('stage') or '?', 'interrupted',
                            '서버가 재시작되어 작업이 끊겼습니다.',
                            retry='같은 단계를 다시 실행하세요. 지금까지의 선택과 답변은 남아 있습니다.')
        store.update(pid, apply)
        return True
    return False
