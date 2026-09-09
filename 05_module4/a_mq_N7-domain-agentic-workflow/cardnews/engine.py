# -*- coding: utf-8 -*-
"""실행 엔진 어댑터 — Claude CLI.

★4강이 정리한 그대로 구현한다.
  · 앱은 «주제와 자료를 받고 진행 상황과 질문을 보여 주는» 쪽
  · 엔진은 «조사와 원고 작성»을 하는 쪽
  · 이어가기는 --resume 에 «저장한 세션 ID»를 넘긴다 (--continue 는 최근 세션을 고르므로 안 쓴다)

★결과를 progress / need_input / result / error 로 «정규화»한다.
  이건 «이 앱이 정하는 규약»이지 CLI 에 내장된 공통 규격이 아니다.

★셸 주입 방지 — 인자 «배열»로만 실행한다. 사용자가 넣은 주제를 명령 문자열에 이어 붙이지 않는다.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time

CLAUDE = shutil.which('claude') or shutil.which('claude.cmd')
DEFAULT_TIMEOUT = 300


_AVAIL = {'at': 0, 'val': None}


def available(max_age=600):
    """설치돼 있는가 «그리고» 실제로 답하는가. 설치만으로 판단하지 않는다.

    ★결과를 캐시한다 — 확인 한 번에 5~25초가 걸린다. 화면을 열 때마다 그걸 기다리게 하지 않는다.
    """
    if _AVAIL['val'] is not None and time.time() - _AVAIL['at'] < max_age:
        return _AVAIL['val']
    v = _check()
    _AVAIL.update({'at': time.time(), 'val': v})
    return v


def _check():
    if not CLAUDE:
        return {'ok': False, 'reason': 'not_installed',
                'detail': 'claude CLI 를 찾지 못했습니다. https://claude.com/claude-code 를 설치하세요.'}
    r = _run(['-p'], timeout=90, prompt='ok 라고만 답해')
    if not r['ok']:
        return {'ok': False, 'reason': r['reason'], 'detail': r['detail']}
    return {'ok': True, 'detail': '인증 확인됨', 'sessionId': r.get('sessionId')}


def _run(args, timeout=DEFAULT_TIMEOUT, cwd=None, prompt=None):
    """claude CLI 를 한 번 호출한다. 예외를 던지지 않고 «항상» dict 를 돌려준다.

    ★★프롬프트는 «stdin» 으로 넘긴다. 인자로 넘기지 않는다.

    실측 2026-09-09 (Windows) — npm 이 만든 `claude.CMD` 배치 셈을 거치면서
    cmd.exe 가 «여러 줄 인자를 첫 줄에서 잘라 먹는다». 784자 프롬프트 중 첫 줄만 전달됐고,
    뒤에 붙인 `--output-format json` 까지 «통째로 무시»돼 모델이 대화체로 답했다.
    ⚠한 줄짜리 시험은 «통과»해서 한참 못 알아챘다 — 그래서 여기 적어 둔다.
    → stdin 으로 주면 그대로 들어간다. 인자 배열만 쓰는 원칙(셸 주입 방지)도 그대로 지킨다.
    """
    if not CLAUDE:
        return {'ok': False, 'reason': 'not_installed', 'detail': 'claude CLI 없음', 'ms': 0}
    cmd = [CLAUDE] + args + ['--output-format', 'json']
    t0 = time.time()
    try:
        if prompt is None:
            p = subprocess.run(cmd, capture_output=True, timeout=timeout, cwd=cwd,
                               stdin=subprocess.DEVNULL, shell=False)
        else:
            p = subprocess.run(cmd, capture_output=True, timeout=timeout, cwd=cwd,
                               input=prompt.encode('utf-8'), shell=False)
    except subprocess.TimeoutExpired:
        return {'ok': False, 'reason': 'timeout',
                'detail': '%d초 안에 답하지 않았습니다' % timeout, 'ms': int((time.time() - t0) * 1000)}
    except Exception as e:
        return {'ok': False, 'reason': 'spawn_failed', 'detail': str(e), 'ms': 0}

    ms = int((time.time() - t0) * 1000)
    out = p.stdout.decode('utf-8', 'replace')
    err = p.stderr.decode('utf-8', 'replace')
    # 경고 줄이 앞에 붙을 수 있으므로 «첫 { 부터» 판다
    i = out.find('{')
    if i < 0:
        low = (out + err).lower()
        if 'login' in low or 'auth' in low or 'api key' in low:
            return {'ok': False, 'reason': 'not_authenticated',
                    'detail': '로그인이 필요합니다. 터미널에서 claude 를 한 번 실행해 로그인하세요.', 'ms': ms}
        return {'ok': False, 'reason': 'no_json', 'detail': (err or out)[:500], 'ms': ms}
    try:
        d = json.loads(out[i:])
    except Exception as e:
        return {'ok': False, 'reason': 'bad_json', 'detail': '%s | %s' % (e, out[i:i + 300]), 'ms': ms}

    if d.get('is_error'):
        return {'ok': False, 'reason': 'engine_error',
                'detail': str(d.get('result'))[:500], 'ms': ms, 'sessionId': d.get('session_id')}
    u = d.get('usage') or {}
    stu = u.get('server_tool_use') or {}
    return {
        'ok': True, 'ms': ms,
        'text': d.get('result') or '',
        'sessionId': d.get('session_id'),
        'turns': d.get('num_turns'),
        'costUsd': d.get('total_cost_usd'),
        'webSearches': stu.get('web_search_requests') or 0,
        'webFetches': stu.get('web_fetch_requests') or 0,
        'usage': {'in': u.get('input_tokens') or 0, 'out': u.get('output_tokens') or 0},
    }


def ask(prompt, session_id=None, tools=None, timeout=DEFAULT_TIMEOUT, cwd=None):
    """엔진에 한 번 묻는다. session_id 를 주면 «같은 대화»를 이어간다."""
    args = ['-p']                       # ★값을 붙이지 않는다 — 프롬프트는 stdin 으로
    if session_id:
        # ⚠--continue 는 «최근» 세션을 고른다. 프로젝트가 여럿이면 섞인다.
        #   앱이 저장한 «명시적 ID» 로만 이어간다.
        args += ['--resume', session_id]
    if tools:
        args += ['--allowedTools'] + list(tools)
    return _run(args, timeout=timeout, cwd=cwd, prompt=prompt)


# ── 모델 응답 파싱 ─────────────────────────────────────────────
FENCE = re.compile(r'```(?:json)?\s*([\s\S]*?)```', re.I)


def extract_json(text):
    """앞뒤 잡담과 코드펜스를 견디고 JSON 한 덩어리를 판다."""
    if not text:
        return None
    t = str(text).strip()
    m = FENCE.search(t)
    if m:
        t = m.group(1).strip()
    try:
        return json.loads(t)
    except Exception:
        pass
    for opener, closer in (('[', ']'), ('{', '}')):
        s = t.find(opener)
        if s < 0:
            continue
        depth, in_str, esc = 0, False, False
        for i in range(s, len(t)):
            c = t[i]
            if esc:
                esc = False
                continue
            if c == '\\':
                esc = True
                continue
            if c == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if c == opener:
                depth += 1
            elif c == closer:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(t[s:i + 1])
                    except Exception:
                        break
    return None


def normalize(payload):
    """엔진이 낸 것을 앱의 규약으로 «해석»한다.

    ★PRD: progress / need_input / result / error 로 정규화.
      이건 우리가 정하는 규약이다. CLI 가 이 필드를 알고 있는 게 아니다.
    """
    if payload is None:
        return {'kind': 'error', 'reason': 'unparsable'}
    if isinstance(payload, list):
        return {'kind': 'result', 'data': payload}
    if not isinstance(payload, dict):
        return {'kind': 'error', 'reason': 'unexpected_type'}
    st = payload.get('status')
    if st == 'need_input' or ('question' in payload and 'options' in payload):
        return {'kind': 'need_input', 'question': {
            'id': payload.get('question_id') or 'q-%d' % int(time.time()),
            'question': payload.get('question') or '',
            'options': payload.get('options') or [],
            'why': payload.get('why') or payload.get('reason') or '',
            'multi': bool(payload.get('multi_select')),
        }}
    if st == 'error':
        return {'kind': 'error', 'reason': payload.get('reason') or 'engine_said_error',
                'detail': payload.get('detail') or ''}
    return {'kind': 'result', 'data': payload}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print('claude 경로:', CLAUDE)
    a = available()
    print('사용 가능:', a)
