# -*- coding: utf-8 -*-
"""배포용 «데모 재생» 묶음을 굽는다.

★왜 만드는가
  요건: 「다른 사람이 **링크만으로 접속해** 워크플로를 실행해 볼 수 있어야 합니다」
  그런데 이 앱은 Claude CLI 를 프로세스로 부르고 로컬 글꼴로 PNG 를 그린다.
  정적 호스팅에는 «실행할 프로세스가 없다». 서버를 빌리면 되지만
  그러면 내 계정 자격증명을 아무나 태울 수 있게 된다(PRD: 키 노출 금지).

  ⇒ CURATOR 와 같은 길을 간다 — **저장된 실제 실행을 재생**한다.
    없는 것을 지어내지 않는다. 있었던 것을 순서대로 드러낼 뿐이다.

★화면 코드는 «하나»다
  static/index.html 을 그대로 복사한다. `?demo=` 가 붙으면 데이터 출처만 바뀐다.
  화면을 두 벌 유지하면 «한쪽만 고쳐지고» 반드시 어긋난다.

만드는 것
  demo/index.html            ← static/index.html 사본
  demo/runs/<name>.json      ← 실행 상태 (세션 ID 가림)
  demo/runs/<name>-manifest.json
  demo/runs/<name>-cards/card-NN.jpg
"""
import io
import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # cardnews/
DEMO = os.path.join(HERE, 'demo')
RUNS = os.path.join(DEMO, 'runs')

# 어떤 실행을 담을지 — (이름, 원본 폴더)
SOURCES = [
    ('news', os.path.join(HERE, 'sample-run')),
    ('myth', os.path.join(HERE, 'sample-run-myth')),
]

# ★가려야 할 것 — 세션 ID 는 재사용될 수 있으므로 배포본에 남기지 않는다
def scrub(st):
    st = dict(st)
    st['sessionId'] = '(가림)'
    for r in st.get('runs', []):
        r.pop('sessionId', None)
    # 로컬 절대경로가 오류 detail 에 박혀 있다 — 남의 화면에 내 폴더 구조를 뿌리지 않는다
    for e in st.get('errors', []):
        d = str(e.get('detail') or '')
        if 'KDT_Works' in d:
            i = d.find('KDT_Works')
            e['detail'] = d[:200].replace(d[max(0, i - 60):i + 200], '…(경로 가림)…') \
                if len(d) > 200 else d
        e['detail'] = str(e.get('detail') or '').replace(os.path.expanduser('~'), '~')
    # 데모에서 「환경」 칸은 실제 로컬 값이므로 «찍힌 시점의 사실»만 남긴다
    st['__health'] = {'engine': {'ok': True}, 'font': '(로컬 확인됨)', 'antigravity': False}
    return st


def main():
    os.makedirs(RUNS, exist_ok=True)

    # ① 화면 — 사본 하나. 두 벌 유지 금지.
    src_ui = os.path.join(HERE, 'static', 'index.html')
    shutil.copy(src_ui, os.path.join(DEMO, 'index.html'))
    print('화면  demo/index.html  ← static/index.html (%d KB)'
          % (os.path.getsize(src_ui) // 1024))

    made = []
    for name, folder in SOURCES:
        ev = os.path.join(folder, 'run-evidence.json')
        if not os.path.exists(ev):
            print('⚠ 건너뜀 — %s 없음' % ev)
            continue
        st = scrub(json.load(io.open(ev, encoding='utf-8')))
        io.open(os.path.join(RUNS, name + '.json'), 'w', encoding='utf-8').write(
            json.dumps(st, ensure_ascii=False, indent=1))

        mf = os.path.join(folder, 'manifest.json')
        if os.path.exists(mf):
            shutil.copy(mf, os.path.join(RUNS, name + '-manifest.json'))

        cd = os.path.join(RUNS, name + '-cards')
        os.makedirs(cd, exist_ok=True)
        n = 0
        for f in sorted(os.listdir(os.path.join(folder, 'cards'))):
            if not f.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
            # 화면은 .jpg 로 찾는다 — 확장자를 맞춘다
            base = os.path.splitext(f)[0]
            shutil.copy(os.path.join(folder, 'cards', f), os.path.join(cd, base + '.jpg'))
            n += 1
        made.append((name, st.get('topic'), len(st.get('cards') or []), n))
        print('실행  runs/%s.json · 카드 %d장' % (name, n))

    # ② 검사 — 화면이 찾는 파일이 «실제로 닿는가»
    print('\n=== 닿는지 검사 ===')
    ok = True
    for name, topic, ncards, nfiles in made:
        for i in range(1, ncards + 1):
            p = os.path.join(RUNS, '%s-cards/card-%02d.jpg' % (name, i))
            if not os.path.exists(p):
                print('  ✗ 없음 %s' % p)
                ok = False
        print('  %-6s %-28s 카드 %d/%d' % (name, topic, nfiles, ncards))
    print('  결과: %s' % ('OK' if ok else '★빠진 파일 있음'))

    total = sum(os.path.getsize(os.path.join(r, f))
                for r, _, fs in os.walk(DEMO) for f in fs)
    print('\n묶음 크기 %.1f MB' % (total / 1024 / 1024))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
