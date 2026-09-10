# -*- coding: utf-8 -*-
"""프로젝트 상태를 «디스크»에 둔다.

★4강이 경고한 그대로 — 브라우저 새로고침과 서버 재시작은 다르다.
  새로고침은 서버 작업이 살아 있지만, 재시작하면 «메모리에 있던 것»은 사라진다.
  그래서 질문·답변·현재 단계·엔진 세션 ID를 «전부» 파일에 둔다.
  세션 ID «만» 저장한다고 화면 상태가 복구되지는 않는다.

쓰기는 여기 한 곳으로 모으고, 임시 파일에 쓴 뒤 «원자적으로 교체»한다.
중간에 끊겨도 반쯤 쓰인 state.json 이 남지 않게.
"""
import json
import os
import re
import threading
import time
import uuid

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
_LOCKS = {}
_LOCKS_GUARD = threading.Lock()

SAFE_ID = re.compile(r'^[A-Za-z0-9_-]{6,40}$')


def _lock(pid):
    with _LOCKS_GUARD:
        if pid not in _LOCKS:
            _LOCKS[pid] = threading.Lock()
        return _LOCKS[pid]


def new_id(prefix='p'):
    return '%s-%s' % (prefix, uuid.uuid4().hex[:12])


def project_dir(pid):
    # ★경로 조작 방지 — 사용자가 준 문자열을 그대로 경로에 붙이지 않는다
    if not SAFE_ID.match(pid or ''):
        raise ValueError('잘못된 프로젝트 ID')
    return os.path.join(ROOT, pid)


def _state_path(pid):
    return os.path.join(project_dir(pid), 'state.json')


def engine_dir(pid):
    """엔진 전용 작업 폴더 — 다른 프로젝트·레포의 맥락이 섞이지 않게."""
    d = os.path.join(project_dir(pid), 'engine')
    os.makedirs(d, exist_ok=True)
    return d


def create(topic, period_days=7, mode='news'):
    pid = new_id('p')
    d = project_dir(pid)
    os.makedirs(os.path.join(d, 'cards'), exist_ok=True)
    os.makedirs(os.path.join(d, 'images'), exist_ok=True)
    # ★엔진이 «여기서» 돌게 한다 (PRD: 작업별 디렉터리를 분리한다).
    #   실측 2026-09-09 — 레포 안에서 돌렸더니 Claude CLI 가 CLAUDE.md 와 git 이력을 읽고
    #   지시 대신 «대화체»로 답했다("최근 커밋을 보니…"). 프롬프트가 프로젝트 컨텍스트에 묻힌다.
    ed = os.path.join(d, 'engine')
    os.makedirs(ed, exist_ok=True)
    st = {
        'projectId': pid,
        'topic': topic,
        # ★모드 — 'news'(최근 소식·웹 검색) | 'myth'(신화 이야기·아카이브 색인)
        #   무엇을 «조사»하고 무엇을 «검증»하는지가 통째로 달라진다. myth.py 머리말 참조.
        'mode': mode if mode in ('news', 'myth') else 'news',
        'periodDays': period_days,
        'createdAt': time.time(),
        'status': 'created',        # created|researching|waiting_for_user|ready|producing|done|error
        'stage': 'research',        # research|select|deep|storyboard|produce|review|export
        'engine': 'claude-cli',
        'sessionId': None,
        'searchedAt': None,
        'candidates': [],
        'selection': [],
        'selectionVersion': 0,
        'question': None,           # {id, version, question, options, why, multi}
        'answers': [],              # [{questionId, version, answer, at}]
        'research': None,           # 심층 조사 기록
        'storyboard': None,         # {version, approved, cards:[…]}
        'cards': [],                # 렌더된 카드
        'runs': [],                 # 작업 기록 (트레이스)
        'requests': {},             # requestId → 결과 (중복 방지)
        'errors': [],
        'exports': None,
    }
    save(st)
    return st


def load(pid):
    p = _state_path(pid)
    if not os.path.exists(p):
        return None
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def save(st):
    """임시 파일에 쓰고 «원자적으로» 교체한다. 반쯤 쓰인 상태가 남지 않게."""
    pid = st['projectId']
    d = project_dir(pid)
    os.makedirs(d, exist_ok=True)
    p = _state_path(pid)
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(st, f, ensure_ascii=False, indent=1)
    # ★실측 2026-09-09 (Windows) — os.replace 가 [WinError 5] 로 터진다.
    #   목적지 파일을 «다른 프로세스가 잠깐 열고 있으면» 교체가 거부된다
    #   (백신·탐색기·앞서 뜬 서버). 락은 «한 프로세스 안»에서만 통한다.
    #   → 잠깐 기다렸다 다시 건다. 그래도 안 되면 «숨기지 않고» 올린다.
    for i in range(6):
        try:
            os.replace(tmp, p)
            return st
        except PermissionError:
            if i == 5:
                raise
            time.sleep(0.15 * (i + 1))
    return st


def update(pid, fn):
    """읽고-고치고-쓰기를 프로젝트별 락 안에서. 동시 요청이 서로를 덮어쓰지 않게."""
    with _lock(pid):
        st = load(pid)
        if st is None:
            raise KeyError(pid)
        fn(st)
        return save(st)


def list_projects():
    if not os.path.isdir(ROOT):
        return []
    out = []
    for x in sorted(os.listdir(ROOT)):
        try:
            st = load(x)
        except ValueError:
            continue
        if st:
            out.append({'projectId': st['projectId'], 'topic': st['topic'],
                        'status': st['status'], 'stage': st['stage'],
                        'createdAt': st['createdAt']})
    return sorted(out, key=lambda x: -x['createdAt'])


# ── 중복 요청 방지 ──────────────────────────────────────────────
# PRD: 「같은 ID·같은 입력은 저장한 결과를 반환하고, 같은 ID·다른 입력은 충돌로 거절한다」
def check_request(st, request_id, payload):
    """(재사용할 결과, 충돌인가) 를 돌려준다."""
    if not request_id:
        return None, False
    rec = st['requests'].get(request_id)
    if rec is None:
        return None, False
    if rec.get('payload') != payload:
        return None, True          # 같은 ID 인데 입력이 다르다 → 충돌
    return rec.get('result'), False


def remember_request(st, request_id, payload, result):
    if request_id:
        st['requests'][request_id] = {'payload': payload, 'result': result, 'at': time.time()}


# ── 트레이스 ────────────────────────────────────────────────────
def add_run(st, kind, **kw):
    """무엇을 왜 했고 무엇이 돌아왔는지. 화면에서 그대로 보여 준다."""
    st['runs'].append({'at': time.time(), 'kind': kind, **kw})
    if len(st['runs']) > 200:
        del st['runs'][:-200]
    return st['runs'][-1]


def add_error(st, where, reason, detail='', retry=None):
    """⚠오류를 «숨기지 않는다». 원인과 «다음에 할 수 있는 것»을 같이 남긴다."""
    st['errors'].append({'at': time.time(), 'where': where, 'reason': reason,
                         'detail': str(detail)[:600], 'retry': retry})
    if len(st['errors']) > 50:
        del st['errors'][:-50]
