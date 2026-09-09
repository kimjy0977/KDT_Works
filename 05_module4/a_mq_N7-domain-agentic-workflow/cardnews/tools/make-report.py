# -*- coding: utf-8 -*-
"""실행 «증거»를 두 가지로 만든다 — 정적 리포트 HTML 과 카드 대지(contact sheet).

★왜 필요한가 — 제출 요건이 「실제 결과물 캡처본 포함」이다.
  브라우저 화면 캡처는 사람이 찍어야 하지만, «실제로 무엇이 나왔는지»는
  실행 기록(run-evidence.json)과 카드 PNG 로 그대로 보여 줄 수 있다.
  이 스크립트는 «지어내지 않고» 그 기록만으로 만든다.

  python tools/make-report.py
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, 'sample-run')

E = lambda s: (str(s if s is not None else '')
               .replace('&', '&amp;').replace('<', '&lt;')
               .replace('>', '&gt;').replace('"', '&quot;'))


def contact_sheet(ev):
    """카드 5장을 한 장으로 — «실제 산출물» 자체가 증거다."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None
    fs = [os.path.join(SRC, 'cards', 'card-%02d.png' % c['n']) for c in ev['cards']]
    fs = [f for f in fs if os.path.exists(f)]
    if not fs:
        return None
    cw, pad, top = 380, 18, 74
    ims = [Image.open(f) for f in fs]
    ch = int(1350 * cw / 1080)
    W = pad + len(ims) * (cw + pad)
    sheet = Image.new('RGB', (W, top + ch + pad), (247, 246, 243))
    d = ImageDraw.Draw(sheet)
    fp = r'C:\Windows\Fonts\malgunbd.ttf'
    try:
        f1 = ImageFont.truetype(fp, 26)
        f2 = ImageFont.truetype(fp, 17)
    except Exception:
        f1 = f2 = ImageFont.load_default()
    d.text((pad, 16), '카드뉴스 에이전트 · 실제 실행 결과', font=f1, fill=(27, 26, 24))
    d.text((pad, 48), '주제 「%s」 · 조사 기준 %s · %d장 · 1080×1350'
           % (ev['topic'], ev.get('searchedAt') or '', len(ims)), font=f2, fill=(107, 102, 96))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((cw, ch), Image.LANCZOS), (pad + i * (cw + pad), top))
    out = os.path.join(SRC, 'cards-contact-sheet.png')
    sheet.save(out, 'PNG', optimize=True)
    return out


def report(ev):
    r = ev.get('research') or {}
    ed = ev.get('editorial') or {}
    sb = ev.get('storyboard') or {}
    runs = ev.get('runs') or []

    def block(title, items, cls):
        if not items:
            return ''
        return ('<h3>%s</h3>' % E(title)) + ''.join(
            '<div class="%s">%s</div>' % (cls, E(x)) for x in items)

    engine_runs = [x for x in runs if x.get('ok') is not None]
    human_runs = [x for x in runs if x.get('kind') == 'human']

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>카드뉴스 에이전트 · 실행 리포트</title><style>
:root{{--bg:#f7f6f3;--card:#fff;--ink:#1b1a18;--dim:#6b6660;--line:#e3dfd8;--accent:#8a5a20;
--ok:#2f6b45;--ok-bg:#e9f3ec;--warn:#9a5b12;--warn-bg:#fbf1e2;--bad:#9b3232;--bad-bg:#fbeaea;--code:#f1eee8}}
@media(prefers-color-scheme:dark){{:root{{--bg:#17161a;--card:#1f1e23;--ink:#eae7e1;--dim:#a49e96;
--line:#34323a;--accent:#d8b47a;--ok:#7fc39a;--ok-bg:#1e2b23;--warn:#e0ab63;--warn-bg:#2c2418;
--bad:#e08585;--bad-bg:#2e1e1e;--code:#26252b}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Malgun Gothic",sans-serif}}
main{{max-width:1040px;margin:0 auto;padding:26px clamp(12px,3vw,26px) 80px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:16px 18px;margin-bottom:14px}}
h1{{font-size:21px;margin:0 0 6px}}h2{{font-size:15px;margin:0 0 10px}}h3{{font-size:13.5px;margin:14px 0 6px}}
.note,.dim{{color:var(--dim);font-size:12.5px}}
.okbox{{background:var(--ok-bg);border-left:3px solid var(--ok);padding:8px 11px;border-radius:0 7px 7px 0;margin:6px 0}}
.warn{{background:var(--warn-bg);border-left:3px solid var(--warn);padding:8px 11px;border-radius:0 7px 7px 0;margin:6px 0}}
.bad{{background:var(--bad-bg);border-left:3px solid var(--bad);padding:8px 11px;border-radius:0 7px 7px 0;margin:6px 0}}
table{{border-collapse:collapse;width:100%;font-size:12.5px}}
th,td{{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}}
th{{background:var(--code)}}.tw{{overflow-x:auto}}
.steps{{display:flex;gap:5px;flex-wrap:wrap;margin:8px 0}}
.st{{font-size:12px;padding:3px 10px;border-radius:20px;border:1px solid var(--ok);
background:var(--ok-bg);color:var(--ok)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px}}
.grid img{{width:100%;border-radius:8px;border:1px solid var(--line);display:block}}
.badge{{display:inline-block;font-size:11.5px;padding:2px 8px;border-radius:20px;font-weight:600}}
.badge.ok{{background:var(--ok-bg);color:var(--ok)}}.badge.warn{{background:var(--warn-bg);color:var(--warn)}}
a{{color:var(--accent)}}img.sheet{{width:100%;border-radius:9px;border:1px solid var(--line)}}
</style></head><body><main>

<div class="card">
<h1>카드뉴스 에이전트 · 실행 리포트</h1>
<p class="note">이 페이지는 <b>실제 실행 기록</b>(<code>sample-run/run-evidence.json</code>)에서 «그대로» 만들어집니다.
손으로 쓴 것이 아닙니다. 생성 스크립트: <code>tools/make-report.py</code></p>
<div class="steps">{''.join('<span class="st">%s</span>' % s for s in
  ['① 조사','② 내가 후보 선택','③ 에이전트가 질문','④ 내가 답변','⑤ 심층 검증','⑥ 기획','⑦ 내가 승인','⑧ 제작','⑨ 부분 수정','⑩ 내려받기'])}</div>
<div class="tw"><table>
<tr><th>주제</th><td>{E(ev['topic'])}</td></tr>
<tr><th>조사 기준</th><td>{E(ev.get('searchedAt'))} · 최근 {ev.get('periodDays')}일</td></tr>
<tr><th>후보</th><td>{len(ev.get('candidates') or [])}개 조사 → <b>{E(', '.join(ev.get('selection') or []))}</b> 선택</td></tr>
<tr><th>독자</th><td>{E((ev.get('answers') or [{{}}])[0].get('answer') if ev.get('answers') else ed.get('audience'))}
 <span class="note">— 에이전트가 «물었고» 사람이 골랐습니다</span></td></tr>
<tr><th>카드</th><td>{len(ev.get('cards') or [])}장 · 1080×1350 · 배경
 {sum(1 for c in (ev.get('cards') or []) if c.get('provenance'))}/{len(ev.get('cards') or [])} 확보</td></tr>
<tr><th>산출물</th><td>{E((ev.get('exports') or {{}}).get('zip'))}
 ({round(((ev.get('exports') or {{}}).get('zipBytes') or 0)/1024/1024,1)} MB) + manifest.json</td></tr>
</table></div></div>

<div class="card"><h2>완성된 카드 {len(ev.get('cards') or [])}장</h2>
<img class="sheet" src="cards-contact-sheet.png" alt="카드 5장">
<div class="grid" style="margin-top:12px">{''.join(
  '<figure style="margin:0"><img src="cards/card-%02d.png" alt=""><figcaption class="note">%d. %s<br>%s</figcaption></figure>'
  % (c['n'], c['n'], E(c.get('title')),
     ('배경 %s · <a href="%s" target="_blank" rel="noopener">출처</a>' %
      (E((c.get('provenance') or {}).get('license')), E((c.get('provenance') or {}).get('pageUrl') or '#')))
     if c.get('provenance') else '<span class="badge warn">배경 없음</span>')
  for c in (ev.get('cards') or []))}</div></div>

<div class="card"><h2>심층 검증 — 확인한 것과 못 한 것을 나눴습니다</h2>
{block('확인한 사실', r.get('verified'), 'okbox')}
{block('발표 주체의 주장', r.get('claims'), 'warn')}
{block('아직 확인 못 한 것', r.get('unverified'), 'bad')}
{block('자료끼리 어긋나는 것', r.get('conflicts'), 'bad')}
<h3>출처</h3>{''.join('<div class="note"><a href="%s" target="_blank" rel="noopener">%s</a> %s</div>'
  % (E(s.get('url')), E(s.get('title') or s.get('url')), E(s.get('published') or ''))
  for s in (r.get('sources') or []))}</div>

<div class="card"><h2>편집 판단</h2><div class="tw"><table>
<tr><th>독자</th><td>{E(ed.get('audience'))} <span class="note">{E(ed.get('why'))}</span></td></tr>
<tr><th>형식</th><td>{E(ed.get('format'))} <span class="note">{E(ed.get('formatWhy'))}</span></td></tr>
<tr><th>표지 후보</th><td>{'<br>'.join(E(h) for h in (ed.get('hooks') or []))}</td></tr>
</table></div></div>

<div class="card"><h2>{E(sb.get('title'))} <span class="note">스토리보드 v{sb.get('version')} · 사람이 승인함</span></h2>
<div class="tw"><table><tr><th>#</th><th>역할</th><th>제목</th><th>핵심</th><th>그림 계획</th></tr>
{''.join('<tr><td>%d</td><td>%s</td><td><b>%s</b></td><td>%s</td><td class="note">%s</td></tr>'
  % (c['n'], E(c.get('role')), E(c.get('title')), E(c.get('body')), E(c.get('imagePlan')))
  for c in (sb.get('cards') or []))}</table></div></div>

<div class="card"><h2>실행 기록 <span class="note">사람이 끼어든 지점을 굵게</span></h2>
<div class="tw"><table><tr><th>주체</th><th>단계</th><th>내용</th><th>소요</th><th>비용</th></tr>
{''.join('<tr><td>%s</td><td>%s</td><td class="note">%s</td><td class="note">%s</td><td class="note">%s</td></tr>'
  % ('<b>사람</b>' if x.get('kind') == 'human' else E(x.get('kind')),
     E(x.get('step')), E(x.get('note') or ('실패: ' + str(x.get('reason'))) if x.get('ok') is False else E(x.get('note'))),
     ('%.1f초' % ((x.get('ms') or 0)/1000)) if x.get('ms') else '',
     ('$%.3f' % x['costUsd']) if x.get('costUsd') else '')
  for x in runs)}</table></div>
<p class="note">엔진 호출 {len(engine_runs)}회 · 사람 개입 {len(human_runs)}회 ·
합계 ${sum(x.get('costUsd') or 0 for x in runs):.2f}</p></div>

<div class="card"><h2>⚠ 남긴 오류 — 숨기지 않았습니다</h2>
{''.join('<div class="bad"><b>%s — %s</b><div class="note">%s</div><div class="note">→ %s</div></div>'
  % (E(e.get('where')), E(e.get('reason')), E(e.get('detail')), E(e.get('retry')))
  for e in (ev.get('errors') or [])) or '<p class="note">없음</p>'}
<p class="note">이 오류들은 «고치기 전» 기록입니다. 원인과 수정은
<a href="README.md">README 「막힌 것과 어떻게 풀었나」</a>에 다섯 건으로 정리했습니다.</p></div>

</main></body></html>"""
    out = os.path.join(SRC, 'run-report.html')
    io.open(out, 'w', encoding='utf-8', newline='\n').write(html)
    return out


def main():
    ev = json.load(io.open(os.path.join(SRC, 'run-evidence.json'), encoding='utf-8'))
    sheet = contact_sheet(ev)
    rep = report(ev)
    print('대지  :', os.path.basename(sheet) if sheet else '(Pillow 없음)',
          '%d KB' % (os.path.getsize(sheet) // 1024) if sheet else '')
    print('리포트:', os.path.basename(rep), '%d KB' % (os.path.getsize(rep) // 1024))
    h = io.open(rep, encoding='utf-8').read()
    assert not [c for c in h if ord(c) < 32 and c not in '\n\t'], '제어문자'
    for tag in ('div', 'table', 'tr', 'td', 'th', 'h1', 'h2', 'h3', 'figure', 'main', 'body', 'html'):
        o, c = h.count('<%s' % tag), h.count('</%s>' % tag)
        assert o == c, '<%s> 불균형 %d/%d' % (tag, o, c)
    print('제어문자 0 · 태그 균형 OK')


main()
