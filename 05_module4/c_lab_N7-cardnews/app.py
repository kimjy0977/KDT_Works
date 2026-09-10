# -*- coding: utf-8 -*-
"""카드뉴스 에이전트 — 웹 서버.

  python app.py            → http://127.0.0.1:8765
  python app.py --port 9000

★127.0.0.1 에만 바인딩한다 (PRD). 실습용 로컬 앱이지 배포물이 아니다.
★긴 HTTP 요청 하나로 전부 끝내지 않는다 — 작업 ID를 «즉시» 돌려주고 화면이 폴링한다.
"""
import argparse
import json
import mimetypes
import os
import shutil
import sys
import threading
import time
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import engine      # noqa: E402
import images      # noqa: E402
import myth        # noqa: E402
import store       # noqa: E402
import workflow    # noqa: E402

STATIC = os.path.join(HERE, 'static')


# ══════════════════════════════════════════════════════════════
def api(handler, method, path, body, query):
    p = path.rstrip('/')

    # ── 환경 점검 — 「설치」와 「인증」을 나눠서 보여 준다
    if p == '/api/health':
        return 200, {
            'engine': engine.available(),
            'font': images.find_font(),
            'antigravity': shutil.which('agy'),   # None 이면 «없다»고 그대로 보여 준다
            'port': handler.server.server_address[1],
        }

    if p == '/api/projects' and method == 'GET':
        return 200, {'projects': store.list_projects()}

    if p == '/api/projects' and method == 'POST':
        topic = (body.get('topic') or '').strip()
        if not topic:
            return 400, {'error': 'topic_required', 'message': '주제를 입력하세요'}
        mode = (body.get('mode') or 'news').strip()
        st = store.create(topic, int(body.get('periodDays') or 7), mode=mode)
        return 200, {'projectId': st['projectId']}

    if p.startswith('/api/projects/'):
        rest = p[len('/api/projects/'):]
        pid, _, tail = rest.partition('/')
        try:
            st = store.load(pid)
        except ValueError:
            return 400, {'error': 'bad_id'}
        if st is None:
            return 404, {'error': 'not_found'}

        # ★서버 재시작으로 끊긴 작업을 «알아본다». 완료로 위장하지 않는다.
        if workflow.recover(pid):
            st = store.load(pid)

        if tail == '' and method == 'GET':
            st['running'] = bool(workflow.is_running(pid))
            return 200, st

        if tail == 'research' and method == 'POST':
            r = _idem(pid, body, {'op': 'research', 'widen': bool(body.get('widen'))},
                      lambda: workflow.run_research(pid, widen=bool(body.get('widen'))))
            return (200 if r.get('ok') is not False else 409), r

        if tail == 'selection' and method == 'POST':
            ids = body.get('candidateIds') or []
            ver = int(body.get('version') or 0)
            if ver != st['selectionVersion']:
                return 409, {'error': 'stale_version', 'message': '화면이 오래됐습니다. 새로고침하세요',
                             'current': st['selectionVersion']}
            if not (1 <= len(ids) <= 3):
                return 400, {'error': 'bad_count', 'message': '1~3개를 고르세요'}
            known = {c['id'] for c in st['candidates']}
            bad = [i for i in ids if i not in known]
            if bad:
                return 400, {'error': 'unknown_candidate', 'message': '목록에 없는 후보: %s' % bad}

            def apply(s):
                s['selection'] = ids
                s['selectionVersion'] += 1
                s['stage'] = 'deep'
                store.add_run(s, 'human', step='selection', note='후보 %d개 선택' % len(ids), picked=ids)
            store.update(pid, apply)
            return 200, {'ok': True, 'selection': ids,
                         'version': store.load(pid)['selectionVersion']}

        if tail == 'deep' and method == 'POST':
            if not st['selection']:
                return 400, {'error': 'no_selection', 'message': '먼저 후보를 고르세요'}
            r = _idem(pid, body, {'op': 'deep', 'sel': st['selection']}, lambda: workflow.run_deep(pid))
            return (200 if r.get('ok') is not False else 409), r

        if tail == 'answers' and method == 'POST':
            q = st.get('question')
            if not q:
                return 409, {'error': 'no_question', 'message': '지금 기다리는 질문이 없습니다'}
            qid, ver = body.get('questionId'), int(body.get('version') or 0)
            # ★오래된 화면의 답변은 «거절»한다 (4강)
            if qid != q['id'] or ver != q.get('version', 1):
                return 409, {'error': 'stale_question',
                             'message': '지난 질문에 대한 답입니다. 현재 작업을 덮어쓰지 않습니다',
                             'current': {'id': q['id'], 'version': q.get('version', 1)}}
            ans = body.get('answer')
            if not ans:
                return 400, {'error': 'empty_answer'}
            reused, conflict = store.check_request(st, body.get('requestId'),
                                                   {'op': 'answer', 'q': qid, 'v': ver, 'a': ans})
            if conflict:
                return 409, {'error': 'request_conflict'}
            if reused is not None:
                return 200, reused          # ★두 번 눌러도 한 번만 반영

            def apply(s):
                s['answers'].append({'questionId': qid, 'version': ver, 'answer': ans, 'at': time.time()})
                s['question'] = None
                s['status'] = 'ready'
                store.add_run(s, 'human', step='answer', note='답변: %s' % ans)
                store.remember_request(s, body.get('requestId'),
                                       {'op': 'answer', 'q': qid, 'v': ver, 'a': ans},
                                       {'ok': True, 'accepted': True})
            store.update(pid, apply)
            workflow.run_deep(pid)          # 같은 세션으로 «이어서» 진행
            return 200, {'ok': True, 'accepted': True}

        if tail == 'storyboard' and method == 'POST':
            n = int(body.get('cards') or 5)
            r = _idem(pid, body, {'op': 'storyboard', 'n': n},
                      lambda: workflow.run_storyboard(pid, n_cards=max(3, min(8, n))))
            return (200 if r.get('ok') is not False else 409), r

        if tail == 'approve' and method == 'POST':
            stage = body.get('stage')
            ver = int(body.get('version') or 0)
            if stage == 'storyboard':
                sb = st.get('storyboard')
                if not sb:
                    return 400, {'error': 'no_storyboard'}
                if ver != sb.get('version'):
                    return 409, {'error': 'stale_version', 'current': sb.get('version')}
                store.update(pid, lambda s: (s['storyboard'].update({'approved': True}),
                                             s.update({'stage': 'produce'}),
                                             store.add_run(s, 'human', step='approve',
                                                           note='스토리보드 v%d 승인' % ver)))
                _produce(pid)
                return 200, {'ok': True, 'producing': True}
            if stage == 'final':
                if not st.get('cards'):
                    return 400, {'error': 'no_cards'}
                store.update(pid, lambda s: (s.update({'stage': 'export', 'status': 'done',
                                                       'finalApprovedAt': time.time()}),
                                             store.add_run(s, 'human', step='approve', note='최종 승인')))
                return 200, _export(pid)
            return 400, {'error': 'bad_stage'}

        # ★취소 — PRD 는 `/api/runs/{id}/cancel` 이라 적었지만 이 앱의 자원은
        #   «프로젝트»다. 경로를 자원에 맞췄고 그 차이를 API_SPEC 에 적어 뒀다.
        if tail == 'cancel' and method == 'POST':
            def run():
                return workflow.cancel(pid)
            return 200, _idem(pid, body, {'op': 'cancel'}, run)

        if tail == 'revisions' and method == 'POST':
            n = body.get('cardNo')
            if not n:
                return 400, {'error': 'card_required'}
            return 200, _revise(pid, int(n), body.get('title'), body.get('body'))

        if tail == 'exports' and method == 'GET':
            if st.get('stage') != 'export':
                return 409, {'error': 'not_approved', 'message': '최종 승인 뒤에 받을 수 있습니다'}
            return 200, st.get('exports') or {}

    return 404, {'error': 'no_route', 'path': p}


def _idem(pid, body, payload, run):
    st = store.load(pid)
    reused, conflict = store.check_request(st, body.get('requestId'), payload)
    if conflict:
        return {'ok': False, 'reason': 'request_conflict'}
    if reused is not None:
        return reused
    r = run()
    if r.get('ok'):
        store.update(pid, lambda s: store.remember_request(s, body.get('requestId'), payload, r))
    return r


# ══════════════════════════════════════════════════════════════
def _produce(pid):
    """스토리보드가 «승인된 뒤에만» 제작을 시작한다."""
    def work():
        st = store.load(pid)
        sb = st['storyboard']
        d = store.project_dir(pid)
        cards = []
        used = set()      # ★한 카드뉴스 안에서 같은 그림을 두 번 쓰지 않는다
        for c in sb['cards']:
            n = c.get('n') or (len(cards) + 1)
            bg = os.path.join(d, 'images', 'bg-%02d.jpg' % n)
            prov, bg_path, got = None, None, None
            if os.path.exists(bg):
                bg_path = bg
            else:
                # ★신화 모드는 검색어를 «모델이 만들지 않는다» — 색인의 작품으로 찍는다.
                if st.get('mode') == 'myth' and c.get('workSlug'):
                    w = next((x for x in myth.index() if x['slug'] == c['workSlug']), None)
                    got = (images.fetch_archive_background(w, os.path.join(d, 'images'),
                                                           'bg-%02d' % n, used=used) if w else
                           {'ok': False, 'reason': 'unknown_slug',
                            'detail': '색인에 없는 slug: %s' % c['workSlug'],
                            'retry': '스토리보드를 다시 만드세요'})
                else:
                    q = c.get('imageQuery') or c.get('imagePlan') or st['topic']
                    got = images.fetch_background(q, os.path.join(d, 'images'), 'bg-%02d' % n)
                if got['ok']:
                    bg_path, prov = got['path'], got['provenance']
                    if prov.get('file'):
                        used.add(prov['file'])
                else:
                    store.update(pid, lambda s, g=got, nn=n: store.add_error(
                        s, 'image', g['reason'], g.get('detail'),
                        retry='카드 %d 의 [이미지 다시] 를 누르세요' % nn))
            out = os.path.join(d, 'cards', 'card-%02d.png' % n)
            # ★출처 줄은 «확인된 것만» 앱이 단다. 모델이 적은 작가·연도는 쓰지 않는다.
            src = c.get('source')
            if prov and prov.get('kind') == 'archive-matched-public-domain':
                src = ((got or {}).get('credit') or {}).get('line') or src
            r = images.render_card(bg_path, out, title=c.get('title') or '',
                                   body=c.get('body') or '', source=src,
                                   n=n, total=len(sb['cards']), role=c.get('role') or '본문')
            cards.append({'n': n, 'role': c.get('role'), 'title': c.get('title'),
                          'body': c.get('body'), 'source': src,
                          'workSlug': c.get('workSlug'),
                          'match': (prov or {}).get('match'),
                          'imagePlan': c.get('imagePlan'), 'imageQuery': c.get('imageQuery'),
                          'bg': os.path.basename(bg_path) if bg_path else None,
                          'provenance': prov,
                          'render': r if r['ok'] else None,
                          'error': None if r['ok'] else r})
        store.update(pid, lambda s: (s.update({'cards': cards, 'stage': 'review',
                                               'status': 'ready'}),
                                     store.add_run(s, 'system', step='produce',
                                                   note='카드 %d장 제작' % len(cards))))
    threading.Thread(target=work, daemon=True).start()


def _revise(pid, n, title, body):
    """★한 장만 고친다. 나머지 승인된 카드는 «그대로» 둔다.
    글자만 바꾸므로 «배경을 다시 받지 않는다» — 해시로 확인한다."""
    st = store.load(pid)
    d = store.project_dir(pid)
    card = next((c for c in st['cards'] if c['n'] == n), None)
    if not card:
        return {'ok': False, 'reason': 'no_card'}
    others = {c['n']: (c.get('render') or {}).get('sha256') for c in st['cards'] if c['n'] != n}
    bg = os.path.join(d, 'images', card['bg']) if card.get('bg') else None
    bg_before = images.sha256(bg) if bg and os.path.exists(bg) else None
    new_t = title if title is not None else card['title']
    new_b = body if body is not None else card['body']
    out = os.path.join(d, 'cards', 'card-%02d.png' % n)
    r = images.render_card(bg, out, title=new_t, body=new_b, source=card.get('source'),
                           n=n, total=len(st['cards']), role=card.get('role') or '본문')
    bg_after = images.sha256(bg) if bg and os.path.exists(bg) else None

    def apply(s):
        for c in s['cards']:
            if c['n'] == n:
                c.update({'title': new_t, 'body': new_b,
                          'render': r if r['ok'] else c.get('render'),
                          'error': None if r['ok'] else r})
        # 수정하면 최종 승인은 «해제»된다 (5강)
        s['stage'] = 'review'
        s['status'] = 'ready'
        s.pop('finalApprovedAt', None)
        s['exports'] = None
        store.add_run(s, 'human', step='revise', note='카드 %d 수정' % n,
                      backgroundUnchanged=(bg_before == bg_after))
    store.update(pid, apply)
    st2 = store.load(pid)
    kept = all(others.get(c['n']) == (c.get('render') or {}).get('sha256')
               for c in st2['cards'] if c['n'] != n)
    return {'ok': r['ok'], 'render': r, 'backgroundUnchanged': bg_before == bg_after,
            'otherCardsUnchanged': kept}


def _export(pid):
    """최종 승인된 «현재 버전»만 내보낸다."""
    st = store.load(pid)
    d = store.project_dir(pid)
    zp = os.path.join(d, 'cardnews.zip')
    manifest = {
        'topic': st['topic'], 'searchedAt': st.get('searchedAt'),
        'periodDays': st.get('periodDays'),
        'audience': (st.get('editorial') or {}).get('audience'),
        'storyboardVersion': (st.get('storyboard') or {}).get('version'),
        'cards': [{'n': c['n'], 'title': c['title'], 'body': c['body'],
                   'source': c.get('source'), 'file': 'card-%02d.png' % c['n'],
                   'image': c.get('provenance')} for c in st['cards']],
        'sources': ((st.get('research') or {}).get('sources') or []),
        'imageNote': ('배경 이미지는 «생성 이미지가 아니라» Wikimedia Commons 의 '
                      'PD/CC 이미지입니다. 각 카드의 image 칸에 출처·라이선스·작가·가져온 날짜가 있습니다. '
                      'Antigravity(agy) 가 이 환경에 없어 AI 이미지 생성 경로는 사용하지 않았습니다.'),
        'exportedAt': time.strftime('%Y-%m-%d %H:%M'),
    }
    with open(os.path.join(d, 'manifest.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        for c in st['cards']:
            fp = os.path.join(d, 'cards', 'card-%02d.png' % c['n'])
            if os.path.exists(fp):
                z.write(fp, 'card-%02d.png' % c['n'])
        z.write(os.path.join(d, 'manifest.json'), 'manifest.json')
    ex = {'zip': 'cardnews.zip', 'zipBytes': os.path.getsize(zp),
          'cards': ['card-%02d.png' % c['n'] for c in st['cards']],
          'manifest': 'manifest.json'}
    store.update(pid, lambda s: s.update({'exports': ex}))
    return {'ok': True, 'exports': ex}


# ══════════════════════════════════════════════════════════════
class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, fmt, *a):
        pass

    def _send(self, code, payload, ctype='application/json; charset=utf-8'):
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8') \
            if ctype.startswith('application/json') else payload
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def _file(self, path, download=False):
        if not os.path.exists(path):
            return self._send(404, {'error': 'not_found'})
        ctype = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        with open(path, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        if download:
            self.send_header('Content-Disposition',
                             'attachment; filename="%s"' % os.path.basename(path))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        p = u.path
        if p.startswith('/api/'):
            try:
                code, out = api(self, 'GET', p, {}, parse_qs(u.query))
            except Exception as e:
                import traceback
                code, out = 500, {'error': 'server', 'detail': traceback.format_exc()[-500:]}
            return self._send(code, out)
        # 프로젝트 산출물
        if p.startswith('/files/'):
            try:
                _, _, pid, rel = p.split('/', 3)
                base = store.project_dir(pid)
                fp = os.path.normpath(os.path.join(base, rel))
                if not fp.startswith(os.path.normpath(base)):   # ★경로 탈출 방지
                    return self._send(400, {'error': 'bad_path'})
                return self._file(fp, download=rel.endswith('.zip'))
            except Exception:
                return self._send(400, {'error': 'bad_path'})
        rel = 'index.html' if p in ('/', '') else p.lstrip('/')
        fp = os.path.normpath(os.path.join(STATIC, rel))
        if not fp.startswith(os.path.normpath(STATIC)):
            return self._send(400, {'error': 'bad_path'})
        return self._file(fp)

    def do_POST(self):
        u = urlparse(self.path)
        n = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(n) if n else b'{}'
        try:
            body = json.loads(raw.decode('utf-8') or '{}')
        except Exception:
            return self._send(400, {'error': 'bad_json'})
        try:
            code, out = api(self, 'POST', u.path, body, parse_qs(u.query))
        except Exception:
            import traceback
            code, out = 500, {'error': 'server', 'detail': traceback.format_exc()[-500:]}
        return self._send(code, out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8765)
    a = ap.parse_args()
    port = a.port
    for attempt in range(6):
        try:
            srv = ThreadingHTTPServer(('127.0.0.1', port), H)   # ★127.0.0.1 에만
            break
        except OSError:
            print('  포트 %d 사용 중 — %d 로 시도합니다' % (port, port + 1))
            port += 1
    else:
        print('빈 포트를 찾지 못했습니다'); return
    print('카드뉴스 에이전트  →  http://127.0.0.1:%d' % port, flush=True)
    print('  한국어 글꼴: %s' % (images.find_font() or '✗ 없음'), flush=True)
    print('  Antigravity: %s' % (shutil.which('agy') or '✗ 없음 → PD/CC 이미지 경로로 진행'), flush=True)

    # ★엔진 점검은 «배경»에서. 확인에 5~25초가 걸리는데 그동안 화면이 안 열리면 안 된다.
    def probe():
        e = engine.available()
        print('  실행 엔진 : %s' % ('사용 가능' if e['ok'] else '✗ ' + str(e.get('detail', ''))), flush=True)
    threading.Thread(target=probe, daemon=True).start()
    srv.serve_forever()


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
