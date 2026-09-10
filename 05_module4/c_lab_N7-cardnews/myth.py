# -*- coding: utf-8 -*-
"""신화 이야기 모드 — 「최근 소식」 대신 «내 아카이브»에서 이야기를 꺼낸다.

★뉴스 모드와 무엇이 다른가

  | | 뉴스 | 신화 |
  |---|---|---|
  | 후보가 어디서 오나 | 웹 검색 — **무엇이 나올지 모른다** | 색인 982점 — **이미 확정된 사실** |
  | 검증할 것 | 「이 소식이 사실인가」 | 「**이 그림이 정말 그 작가 것인가**」 |
  | 모델의 몫 | 찾기 + 요약 | **이야기하기.** 목록·개수는 모델이 만들지 않는다 |

★그래서 이 파일이 하는 일은 **모델이 지어낼 자리를 줄이는 것**이다.
  후보 목록과 작품 수는 «세어서» 넣고, 모델에게는 「이 사실로 이야기를 써라」만 시킨다.
  (CURATOR 의 autoRepair 와 같은 원칙 — **조회는 대신 해 주고, 판단은 대신 하지 않는다.**)

★★실측 2026-09-09 — 이 파일이 존재하는 진짜 이유
  원제만으로 Commons 를 찍으면 **PD 이미지는 5/5 찾는데 «작가가 다르다».**

    넣은 것                  색인상 작가        Commons 가 준 것
    Pygmalion and Galatea    팔코네            제롬
    The Birth of Venus       보티첼리          카바넬
    Narcissus                카라바조          워터하우스

  **같은 «이야기»의 다른 «그림»이다.** 그대로 두면 카드에 「보티첼리」라 적고
  카바넬 그림을 싣게 된다 — 「찾았다」와 「**맞는 걸** 찾았다」는 다른 사실이다.
  (5강의 「요청을 보냈다 ≠ 파일이 생겼다」와 같은 종류의 함정이다.)
  → 작가명을 영문으로 풀어 **함께** 찍고, 맞았는지를 `match` 로 «기록»한다.
    못 맞추면 **맞춘 척하지 않고** `same-story` 로 내려 적는다.
"""
import io
import json
import os
import re
import threading
import time
import unicodedata
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
# ★색인은 «어디 있을지 모른다» — 폴더가 옮겨질 수 있다.
#   실습(c_lab)과 메인퀘(a_mq)를 가르면서 상대 경로가 깨졌다(2026-09-10).
#   ⇒ 한 곳을 «박아 두지» 않고 후보를 차례로 본다. 그리고 «어느 것을 썼는지» 말한다.
INDEX_CANDIDATES = [
    os.path.join(HERE, 'data', 'works-index.json'),                 # 자기 폴더
    os.path.join(HERE, os.pardir, 'data', 'works-index.json'),      # 부모 (옛 위치)
    os.path.join(HERE, os.pardir, 'a_mq_N7-domain-agentic-workflow',
                 'data', 'works-index.json'),                       # 형제 (분리 후)
]
INDEX_PATH = next((p for p in INDEX_CANDIDATES if os.path.exists(p)), INDEX_CANDIDATES[-1])
CACHE_DIR = os.path.join(HERE, 'data', '_cache')
ARTIST_CACHE = os.path.join(CACHE_DIR, 'artists-en.json')

UA = 'KDT-MQ4-CardNews/1.0 (https://github.com/kimjy0977/KDT_Works; kjuyoung77@gmail.com)'

_INDEX = None
_LOCK = threading.Lock()


# ════════════════════════════════════════════════════════════
# 색인
# ════════════════════════════════════════════════════════════
def index():
    """아카이브 색인을 읽는다. 없으면 «없다고 말한다» — 빈 목록으로 넘어가지 않는다."""
    global _INDEX
    with _LOCK:
        if _INDEX is None:
            if not os.path.exists(INDEX_PATH):
                # ★«어디를 봤는지»까지 말한다. 「없다」만 던지면 고칠 수가 없다.
                raise FileNotFoundError(
                    '아카이브 색인을 찾을 수 없습니다. 본 곳: '
                    + ' | '.join(INDEX_CANDIDATES)
                    + ' → tools/build-index.py 로 먼저 만드세요')
            with io.open(INDEX_PATH, encoding='utf-8') as f:
                _INDEX = json.load(f)
        return _INDEX


def _norm(s):
    """비교용 정규화 — 발음기호를 벗기고 소문자로. (Étienne → etienne)

    ★실측 2026-09-09 — NFKD 만 걸고 끝내면 «한글이 통째로 사라진다».
      NFKD 는 한글 음절도 자모로 쪼갠다(피 → U+1111 U+1175).
      자모는 결합문자가 아니라 필터를 통과하는데, 뒤의 `가-힣` 정규식이 그걸 지운다.
      → 결과가 빈 문자열이 되어 find_story() 가 «매번 None» 을 돌려줬다.
      쪼갠 뒤에는 **반드시 NFC 로 다시 합친다.**
    """
    s = unicodedata.normalize('NFKD', str(s or ''))
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = unicodedata.normalize('NFC', s)          # ★한글 되붙이기
    return re.sub(r'[^a-z0-9가-힣 ]+', ' ', s.lower()).strip()


def clusters(myth='그리스로마', min_works=2, limit=14):
    """★이야기 후보를 «센다». 모델이 만들지 않는다.

    두 인물이 «같은 작품에 함께» 등장하면 그건 하나의 이야기다
    (피그말리온 × 갈라테이아 · 페르세우스 × 메두사 …).
    작품 수가 많은 순으로 준다 — 그림이 많아야 카드뉴스가 된다.
    """
    import itertools
    pool = [w for w in index() if (w.get('mythKo') or '') == myth]
    bag = {}
    for w in pool:
        ppl = sorted(set(p for p in (w.get('people') or []) if p))
        for a, b in itertools.combinations(ppl, 2):
            bag.setdefault((a, b), []).append(w)
    rows = []
    for (a, b), ws in bag.items():
        if len(ws) < min_works:
            continue
        artists = sorted({w['artist'] for w in ws if w.get('artist')})
        rows.append({
            'people': [a, b],
            'works': len(ws),
            'artists': artists,
            'eras': sorted({(w.get('era') or '').split()[0] for w in ws if w.get('era')}),
            'titles': [w['title'] for w in ws][:6],
        })
    rows.sort(key=lambda r: (-r['works'], r['people'][0]))
    rows = rows[:limit]
    for i, r in enumerate(rows):
        r['id'] = 'c%d' % (i + 1)
    return rows


def works_of(people):
    """이야기(인물 짝)에 해당하는 작품 전체를 «색인 그대로» 돌려준다."""
    want = set(people or [])
    out = [w for w in index() if want.issubset(set(w.get('people') or []))]
    out.sort(key=lambda w: (w.get('era') or '', w.get('inception') or ''))
    return out


def find_story(topic, myth='그리스로마'):
    """주제 문자열이 특정 이야기를 «이미 지목»하고 있으면 그것을 찾는다.

    "피그말리온과 갈라테이아" 처럼 주제가 구체적이면 후보를 고를 필요가 없다.
    """
    t = _norm(topic)
    if not t:
        return None
    best = None
    for c in clusters(myth=myth, min_works=1, limit=400):
        hit = sum(1 for p in c['people'] if _norm(p) and _norm(p) in t)
        if hit and (best is None or (hit, c['works']) > (best[0], best[1]['works'])):
            best = (hit, c)
    return best[1] if best else None


# ════════════════════════════════════════════════════════════
# 작가명 한국어 → 영문 (Wikidata)
# ════════════════════════════════════════════════════════════
def _get_json(url, timeout=30, tries=3):
    """★429 를 만나면 «기다렸다가» 다시 건다. 실측 2026-09-09 — 8건 연속 조회에서 6번째에 429."""
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Api-User-Agent': UA})
            return json.load(urllib.request.urlopen(req, timeout=timeout))
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 503):
                time.sleep(1.5 * (2 ** i))
                continue
            raise
        except Exception as e:
            last = e
            time.sleep(1.0 * (i + 1))
    raise last


def _cache_load():
    try:
        with io.open(ARTIST_CACHE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _cache_save(d):
    os.makedirs(CACHE_DIR, exist_ok=True)
    tmp = ARTIST_CACHE + '.tmp'
    with io.open(tmp, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, ARTIST_CACHE)


ARTIST_WORDS = ('화가', '조각가', '판화', '예술가', '미술가',
                'painter', 'sculptor', 'artist', 'engraver', 'draughtsman')


def _name_variants(ko):
    """★한 칸 차이로 0건이 난다 — 표기 변형을 «만들어» 준다.

    실측 2026-09-09
      `장 레옹 제롬`   → 0건.  Wikidata 라벨은 **`장레옹 제롬`**(이름만 붙임)
      `안뇰로 브론치노` → 0건.  **`브론치노`** 만 넣으면 Q7803
    `wbsearchentities` 는 **라벨 접두 일치**라 정확히 안 맞으면 그냥 없다고 한다
    (CURATOR 의 label/fulltext 함정과 같은 종류다).
    """
    ko = re.sub(r'\s+', ' ', (ko or '').strip())
    if not ko:
        return []
    out = [ko]
    parts = ko.split(' ')
    if len(parts) > 2:                       # 이름은 붙이고 성만 띄운다
        out.append(''.join(parts[:-1]) + ' ' + parts[-1])
    if len(parts) > 1:                       # 성만
        out.append(parts[-1])
    seen, uniq = set(), []
    for v in out:
        if v and v not in seen:
            seen.add(v)
            uniq.append(v)
    return uniq


def artist_en(ko):
    """한국어 작가명 → 영문 이름. 못 찾으면 None — «지어내지 않는다».

    ⚠검색 결과가 «사람이 맞는지»를 설명으로 거른다.
      `제롬` 만 넣으면 미국 아이다호주의 «도시»가 1순위로 온다(실측).
      그대로 받으면 카드에 도시 이름을 작가로 적게 된다.
    """
    ko = (ko or '').strip()
    if not ko:
        return None
    cache = _cache_load()
    if ko in cache:
        return cache[ko]        # None 도 캐시한다 — 없는 걸 매번 다시 묻지 않게
    en = None
    try:
        for v in _name_variants(ko):
            u = ('https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json'
                 '&language=ko&uselang=ko&type=item&limit=5&search=' + urllib.parse.quote(v))
            for h in (_get_json(u).get('search') or []):
                desc = (h.get('description') or '').lower()
                if not any(w in desc for w in ARTIST_WORDS):
                    continue    # ★사람(예술가)이 아닌 것은 버린다
                qid = h['id']
                e = _get_json('https://www.wikidata.org/w/api.php?action=wbgetentities'
                              '&format=json&props=labels&languages=en&ids=' + qid)
                en = ((e.get('entities', {}).get(qid, {}).get('labels', {}) or {})
                      .get('en', {}) or {}).get('value')
                if en:
                    break
            if en:
                break
    except Exception:
        return None             # ★실패는 캐시하지 않는다 — 네트워크 탓일 수 있다
    cache[ko] = en
    _cache_save(cache)
    return en


def _surnames(name):
    """비교에 쓸 «성»을 뽑는다. 이름 전체가 같기를 기대하면 거의 안 맞는다.

    'Jean-Léon Gérôme' → {jean, leon, gerome} 중 3글자 이상만.
    """
    return {t for t in _norm(name).split() if len(t) >= 3}


def wikidata_artwork(title_en, en_artist):
    """★작품 «항목»을 찾아 대표 이미지(P18)를 얻는다. 검색보다 훨씬 정확하다.

    Commons 전문 검색은 «부분 확대 컷»을 아무렇지 않게 1순위로 준다.
    실측 2026-09-09 — 브론치노 「피그말리온과 갈라테이아」를 찾으니
    **제단의 황소만 크게 잡은 컷**이 왔다. 파일명에 detail 이 없어 못 걸렀다.

    Wikidata 는 **같은 제목이라도 작가마다 별개 항목**을 둔다.
      Pygmalion and Galatea → Q111577849(브론치노) · Q17305070(제롬) · Q17315628(팔코네)
    그래서 P170(제작자)로 «어느 것인지» 가릴 수 있고, P18 은 그 작품의 대표 이미지다.

    ⛔작가를 모르면(en_artist 없음) 이 경로를 «쓰지 않는다» — 가릴 수가 없다.
    """
    if not title_en or not en_artist:
        return None
    want = _surnames(en_artist)
    if not want:
        return None
    try:
        u = ('https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json'
             '&language=en&uselang=en&type=item&limit=10&search=' + urllib.parse.quote(title_en))
        ids = [h['id'] for h in (_get_json(u).get('search') or [])]
        if not ids:
            return None
        e = _get_json('https://www.wikidata.org/w/api.php?action=wbgetentities&format=json'
                      '&props=claims&ids=' + '|'.join(ids[:10]))
        cand = []
        for qid, ent in (e.get('entities') or {}).items():
            cl = ent.get('claims') or {}
            img = next((c['mainsnak'].get('datavalue', {}).get('value')
                        for c in (cl.get('P18') or []) if c['mainsnak'].get('datavalue')), None)
            cre = next((c['mainsnak'].get('datavalue', {}).get('value', {}).get('id')
                        for c in (cl.get('P170') or []) if c['mainsnak'].get('datavalue')), None)
            if img and cre:
                cand.append((qid, cre, img))
        if not cand:
            return None
        lab = _get_json('https://www.wikidata.org/w/api.php?action=wbgetentities&format=json'
                        '&props=labels&languages=en&ids='
                        + '|'.join(sorted({c[1] for c in cand})[:12]))
        names = {k: ((v.get('labels', {}).get('en', {}) or {}).get('value') or '')
                 for k, v in (lab.get('entities') or {}).items()}
        for qid, cre, img in cand:
            if want & _surnames(names.get(cre)):
                return {'qid': qid, 'file': img, 'creator': names.get(cre)}
    except Exception:
        return None
    return None


# ════════════════════════════════════════════════════════════
# 그림 찾기 — «맞았는지»까지 기록한다
# ════════════════════════════════════════════════════════════
def find_painting(work, commons_search, limit=8, used=None, commons_file=None):
    """색인의 작품 한 점에 대응하는 Commons 이미지를 찾는다.

    commons_search 를 «주입»받는다 — images.py 의 라이선스 판정을 그대로 쓰되
    이 모듈이 images 를 되import 하지 않게 (순환 참조 방지).

    반환에 반드시 `match` 가 있다 — ★넷이다:
      'exact'            작가가 «일치»한다 — 색인이 말한 바로 그 작품
      'different-artist' 작가를 풀었는데 «불일치» — 같은 이야기의 다른 화가다
      'unverified'       ★작가 영문명을 «못 얻어» 대조 자체를 못 했다
      'none'             쓸 수 있는 이미지가 없다

    ★★`different-artist` 와 `unverified` 를 하나로 묶지 않는다.
      처음엔 둘 다 `same-story` 로 적었다가 **제롬 그림을 제대로 찾고도**
      「다른 화가」로 내려 적는 것을 봤다(실측 2026-09-09).
      **「틀렸다」와 「모른다」는 다른 사실이다.** 섞으면 성능을 스스로 깎아 보고하게 된다.

    ⛔ 어느 쪽이든 exact 로 올려 적지 않는다. 그게 이 함수의 존재 이유다.
    """
    orig = (work.get('origTitle') or work.get('title') or '').strip()
    # ★괄호 안 부기는 Commons 에 없다 — "Pygmalion and Galatea (Side View)" 로는 못 찾는다
    bare = re.sub(r'\s*[\(（][^)）]*[\)）]', '', orig).strip()
    ko_artist = (work.get('artist') or '').strip()
    en_artist = artist_en(ko_artist)

    # ★질의를 «좁은 것부터» 넣는다 — 원제+작가가 맞으면 그게 정답이다.
    tries = []
    for q in ('%s %s' % (bare, en_artist) if (bare and en_artist) else None,
              en_artist,                 # 작가만으로도 그 사람 그림이 나온다
              orig if orig != bare else None,
              bare):                     # 최후 — 같은 이야기의 «아무» 그림
        if q and q not in tries:
            tries.append(q)

    want = _surnames(en_artist) if en_artist else set()
    used = set(used or ())          # ★이미 다른 카드가 쓴 파일은 «다시 쓰지 않는다»
    fallback, attempts = None, []

    # ── ①순위: Wikidata 작품 항목의 대표 이미지 ─────────────────
    if commons_file and en_artist:
        wd = wikidata_artwork(bare, en_artist)
        attempts.append({'query': 'wikidata:P18 «%s» + %s' % (bare, en_artist),
                         'ok': bool(wd), 'n': 1 if wd else 0})
        if wd and ('File:' + wd['file']) not in used and wd['file'] not in used:
            info = commons_file(wd['file'])
            for r in (info.get('results') or []):
                if (r.get('verdict') in ('pd', 'cc') and r.get('imageUrl')
                        and r.get('title') not in used
                        and not str(r.get('mime') or '').endswith(('gif', 'pdf', 'djvu'))):
                    return {'ok': True, 'match': 'exact', 'pick': r, 'via': 'wikidata-p18',
                            'artistEn': en_artist, 'qid': wd['qid'], 'attempts': attempts}

    def _rank(r):
        """★큰 그림을 먼저. 실측 2026-09-09 — 「File:Gérôme details.jpg」 같은
        «부분 확대 컷»이 26KB 로 걸려 배경이 흐릿하게 나왔다.
        작가는 맞았지만 «쓸 만한 그림»은 아니었다 — 맞음과 쓸모는 다르다."""
        area = (r.get('width') or 0) * (r.get('height') or 0)
        penalty = 1 if re.search(r'detail|crop|sketch|study', str(r.get('title') or ''), re.I) else 0
        return (penalty, -area)

    for q in tries:
        s = commons_search(q, limit=limit)
        attempts.append({'query': q, 'ok': bool(s.get('ok')),
                         'n': len(s.get('results') or []) if s.get('ok') else 0})
        if not s.get('ok'):
            continue
        usable = [r for r in (s.get('results') or [])
                  if r.get('verdict') in ('pd', 'cc') and r.get('imageUrl')
                  and not str(r.get('mime') or '').endswith(('gif', 'pdf', 'djvu'))
                  and r.get('title') not in used]
        usable.sort(key=_rank)
        for r in usable:
            # 파일 제목과 작가 표기 «둘 다» 본다 — Artist 칸이 비어 있는 파일이 많다
            hay = _surnames(r.get('author')) | _surnames(r.get('title'))
            if want and (want & hay):
                return {'ok': True, 'match': 'exact', 'pick': r, 'via': 'commons-search',
                        'artistEn': en_artist, 'attempts': attempts}
        if usable and fallback is None:
            fallback = usable[0]

    if fallback is not None:
        if want:
            return {'ok': True, 'match': 'different-artist', 'pick': fallback,
                    'artistEn': en_artist, 'attempts': attempts,
                    'note': ('색인의 작가(%s)와 «다른» 화가의 그림입니다. '
                             '같은 이야기를 그린 다른 작품이므로 카드에는 '
                             'Commons 가 밝힌 작가를 적습니다.' % (ko_artist or '미상'))}
        return {'ok': True, 'match': 'unverified', 'pick': fallback,
                'artistEn': None, 'attempts': attempts,
                'note': ('작가 「%s」의 영문 표기를 찾지 못해 **대조하지 못했습니다.** '
                         '맞을 수도 아닐 수도 있으므로 카드에는 '
                         'Commons 가 밝힌 작가만 적습니다.' % (ko_artist or '미상'))}

    return {'ok': False, 'match': 'none', 'artistEn': en_artist, 'attempts': attempts,
            'reason': 'no_usable_license',
            'detail': '시도한 검색어: %s' % ' / '.join(tries),
            'retry': '다른 작품을 고르거나 검색어를 바꿔 다시 시도하세요'}


def credit(work, found):
    """카드에 «실제로 적을» 출처 한 줄. 색인과 Commons 를 섞지 않는다.

    ★exact 일 때만 색인의 작가·연도·소장처를 쓴다.
      same-story 면 Commons 가 밝힌 작가만 쓴다 — 모르는 것은 적지 않는다.
    """
    if not found or not found.get('ok'):
        return None
    pick = found['pick']
    if found['match'] == 'exact':
        bits = [work.get('title'), work.get('artist'), work.get('inception')]
        line = ' · '.join(b for b in bits if b)
        return {'line': line, 'basis': 'archive',
                'collection': work.get('collection'), 'material': work.get('material'),
                'file': pick.get('title'), 'license': pick.get('license')}
    author = (pick.get('author') or '').strip() or '작가 표기 없음'
    return {'line': '%s (Wikimedia Commons)' % author, 'basis': 'commons',
            'collection': None, 'material': None,
            'file': pick.get('title'), 'license': pick.get('license'),
            'note': found.get('note')}
