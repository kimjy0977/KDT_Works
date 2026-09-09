# -*- coding: utf-8 -*-
"""이미지 확보와 카드 렌더링.

★PRD 는 Antigravity CLI(agy) 로 «생성»하는 것을 기본안으로 둔다.
  그런데 이 환경에 agy 가 «설치돼 있지 않다»(DECISIONS D-03).
  PRD 5절이 「이용 불가 시 성공한 척하지 않는다」·「확인하지 않은 명령을 만들지 않는다」고 했으므로
  ⛔ agy 를 호출하는 척하지 않고, PRD 가 «명시적으로 허용한» CC0·퍼블릭 도메인 경로로 간다.
  → Wikimedia Commons 에서 라이선스를 «확인해서» 가져오고 출처를 기록한다.

★글자는 이미지와 «완전히 분리»한다 (5강).
  배경 파일은 그대로 두고 텍스트를 얹어 최종 카드를 만든다.
  그래서 «텍스트만 고칠 때 배경을 다시 받지 않아도» 된다 — 그 사실을 해시로 검사한다.
"""
import hashlib
import io as _io
import json
import os
import shutil
import time
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw, ImageFont

UA = 'KDT-MQ4-CardNews/1.0 (https://github.com/kimjy0977/KDT_Works; kjuyoung77@gmail.com)'
W, H = 1080, 1350          # DECISIONS D-05

HERE = os.path.dirname(os.path.abspath(__file__))

# 한국어 글꼴 — 없으면 «없다고 말한다». 깨진 네모로 렌더하지 않는다.
FONT_CANDIDATES = [
    r'C:\Windows\Fonts\malgunbd.ttf', r'C:\Windows\Fonts\malgun.ttf',
    r'C:\Windows\Fonts\NanumGothicBold.ttf', r'C:\Windows\Fonts\NanumGothic.ttf',
    '/System/Library/Fonts/AppleSDGothicNeo.ttc',
    '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf',
]


def find_font():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Api-User-Agent': UA})
    return urllib.request.urlopen(req, timeout=timeout)


def commons_search(query, limit=3):
    """Commons 에서 이미지를 찾고 «라이선스를 확인»한다.

    반환: [{title, imageUrl, license, licenseUrl, author, verdict, pageUrl}]
      verdict ∈ pd | cc | restricted | unknown
      ⚠unknown·restricted 는 쓰지 않는다.
    """
    try:
        su = ('https://commons.wikimedia.org/w/api.php?action=query&format=json'
              '&list=search&srnamespace=6&srlimit=%d&srsearch=%s'
              % (limit, urllib.parse.quote(query)))
        hits = json.load(_get(su)).get('query', {}).get('search', [])
    except Exception as e:
        return {'ok': False, 'reason': 'search_failed', 'detail': str(e)}
    if not hits:
        return {'ok': True, 'results': [], 'empty': True}

    titles = '|'.join(h['title'] for h in hits)
    try:
        # ★iiurlwidth 를 주면 Commons 가 «래스터 썸네일» URL 을 함께 준다.
        #   실측 2026-09-09 — 원본 url 을 그대로 받았더니 SVG 가 걸려
        #   Pillow 가 "cannot identify image file" 로 세 장을 놓쳤다.
        #   썸네일은 SVG·거대 TIFF 도 PNG/JPEG 로 내려온다.
        iu = ('https://commons.wikimedia.org/w/api.php?action=query&format=json'
              '&titles=%s&prop=imageinfo&iiprop=url%%7Cextmetadata%%7Cmime&iiurlwidth=1600'
              % urllib.parse.quote(titles))
        pages = json.load(_get(iu)).get('query', {}).get('pages', {})
    except Exception as e:
        return {'ok': False, 'reason': 'info_failed', 'detail': str(e)}

    import re as _re
    strip = lambda s: _re.sub(r'<[^>]*>', '', str(s or '')).strip()
    out = []
    for p in pages.values():
        info = (p.get('imageinfo') or [{}])[0]
        em = info.get('extmetadata') or {}
        lic = strip(em.get('LicenseShortName', {}).get('value'))
        low = lic.lower()
        verdict = ('pd' if ('public domain' in low or low.startswith('pd') or 'cc0' in low)
                   else 'cc' if low.startswith('cc by')
                   else 'restricted' if lic else 'unknown')
        out.append({
            'title': p.get('title'),
            # 썸네일이 있으면 그것을 쓴다 — SVG·초대형 파일도 래스터로 내려온다
            'imageUrl': info.get('thumburl') or info.get('url'),
            'originalUrl': info.get('url'), 'mime': info.get('mime'),
            'pageUrl': info.get('descriptionurl'),
            'license': lic or None, 'licenseUrl': strip(em.get('LicenseUrl', {}).get('value')) or None,
            'author': strip(em.get('Artist', {}).get('value')) or None,
            'verdict': verdict,
        })
    return {'ok': True, 'results': out}


def fetch_background(query, dest_dir, name):
    """쓸 수 있는 라이선스의 이미지 «하나»를 받아 배경으로 저장한다.

    ★「요청을 보냈다」와 「파일이 생겼다」는 다른 사실이다(5강).
      실제로 열리는 이미지인지까지 확인한 뒤에만 성공으로 돌려준다.
    """
    # ★질의를 «단계적으로 줄여» 가며 찾는다.
    #   실측 2026-09-09 — 모델이 낸 10단어짜리 장면 묘사("europe map france startup
    #   investment arrow from korea illustration")로는 Commons 가 «0건»을 준다.
    #   Commons 검색은 문헌 검색이라 낱말이 많을수록 좁아진다. 짧게 줄이면 걸린다.
    words = [w for w in str(query or '').replace(',', ' ').split() if len(w) > 2]
    tries = []
    for n in (len(words), 4, 3, 2):
        q = ' '.join(words[:n]).strip()
        if q and q not in tries:
            tries.append(q)
    usable, pick, s = [], None, {'results': []}
    for q in tries:
        s = commons_search(q, limit=6)
        if not s.get('ok'):
            continue
        usable = [r for r in s.get('results', [])
                  if r['verdict'] in ('pd', 'cc') and r.get('imageUrl')
                  # ★애니메이션·문서 스캔은 배경으로 못 쓴다
                  and not str(r.get('mime') or '').endswith(('gif', 'pdf', 'djvu'))]
        if usable:
            pick = usable[0]
            break
    if not pick:
        return {'ok': False, 'reason': 'no_usable_license',
                'detail': 'PD/CC 이미지를 못 찾았습니다. 시도한 검색어: %s' % ' / '.join(tries),
                'retry': '카드의 이미지 검색어를 더 짧게(2~3단어) 바꿔 다시 시도하세요'}
    os.makedirs(dest_dir, exist_ok=True)
    path = os.path.join(dest_dir, name + '.jpg')
    try:
        raw = _get(pick['imageUrl'], timeout=60).read()
        im = Image.open(_io.BytesIO(raw))       # ★실제로 «열리는» 이미지인지 확인
        im = im.convert('RGB')
        im.thumbnail((2000, 2000))
        im.save(path, 'JPEG', quality=88)
    except Exception as e:
        return {'ok': False, 'reason': 'download_or_decode_failed', 'detail': str(e),
                'retry': '다시 시도하세요'}
    if not os.path.exists(path) or os.path.getsize(path) < 2000:
        return {'ok': False, 'reason': 'file_too_small', 'detail': '파일이 만들어지지 않았습니다',
                'retry': '다시 시도하세요'}
    return {'ok': True, 'path': path, 'bytes': os.path.getsize(path),
            'sha256': sha256(path), 'provenance': {
                'kind': 'public-domain-or-cc',      # ★«생성 이미지가 아니다»
                'source': 'Wikimedia Commons',
                'file': pick['title'], 'pageUrl': pick['pageUrl'],
                'imageUrl': pick['imageUrl'], 'license': pick['license'],
                'licenseUrl': pick['licenseUrl'], 'author': pick['author'],
                'verdict': pick['verdict'], 'fetchedAt': time.strftime('%Y-%m-%d %H:%M'),
                'generator': None, 'prompt': None,   # 생성 이미지가 아니므로 «해당 없음»
            }}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(65536), b''):
            h.update(b)
    return h.hexdigest()[:16]


# ── 렌더링 ──────────────────────────────────────────────────────
def _wrap(draw, text, font, max_w):
    """한국어는 «어절» 단위로 접는다. 어절 하나가 넘치면 글자 단위로."""
    lines, cur = [], ''
    for word in str(text or '').split():
        t = (cur + ' ' + word).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
            continue
        if cur:
            lines.append(cur)
        if draw.textlength(word, font=font) <= max_w:
            cur = word
        else:
            piece = ''
            for ch in word:
                if draw.textlength(piece + ch, font=font) <= max_w:
                    piece += ch
                else:
                    lines.append(piece)
                    piece = ch
            cur = piece
    if cur:
        lines.append(cur)
    return lines


def render_card(bg_path, out_path, *, title, body, source=None, n=None, total=None,
                role='본문', badge=None):
    """배경 «위에» 글자를 얹는다. 배경 파일은 «건드리지 않는다»."""
    font_path = find_font()
    if not font_path:
        return {'ok': False, 'reason': 'no_korean_font',
                'detail': '한국어 글꼴을 찾지 못했습니다. 깨진 글자로 만들지 않고 멈춥니다.',
                'retry': '맑은 고딕 또는 나눔고딕을 설치하세요'}

    card = Image.new('RGB', (W, H), (17, 16, 20))
    if bg_path and os.path.exists(bg_path):
        bg = Image.open(bg_path).convert('RGB')
        r = max(W / bg.width, H / bg.height)
        bg = bg.resize((int(bg.width * r + 1), int(bg.height * r + 1)), Image.LANCZOS)
        card.paste(bg, ((W - bg.width) // 2, (H - bg.height) // 2))

    # 글자가 읽히도록 아래쪽을 어둡게 — «대비»는 5강 검수 항목이다
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for i in range(H):
        a = 0 if i < H * 0.30 else int(235 * min(1.0, (i - H * 0.30) / (H * 0.40)))
        od.line([(0, i), (W, i)], fill=(10, 9, 12, a))
    card = Image.alpha_composite(card.convert('RGBA'), ov).convert('RGB')

    d = ImageDraw.Draw(card)
    big = ImageFont.truetype(font_path, 74 if role == '표지' else 62)
    mid = ImageFont.truetype(font_path, 40)
    small = ImageFont.truetype(font_path, 27)
    pad = 84
    maxw = W - pad * 2

    y = H - pad
    if source:
        src = str(source)[:78]
        d.text((pad, y - 30), '출처 ' + src, font=small, fill=(186, 182, 176))
        y -= 52
    if body:
        bl = _wrap(d, body, mid, maxw)[:6]
        for line in reversed(bl):
            y -= 56
            d.text((pad, y), line, font=mid, fill=(238, 235, 229))
        y -= 22
    tl = _wrap(d, title, big, maxw)[:4]
    for line in reversed(tl):
        y -= (86 if role == '표지' else 74)
        d.text((pad, y), line, font=big, fill=(255, 253, 248))
    if badge:
        y -= 56
        d.rectangle([pad, y, pad + d.textlength(badge, font=small) + 34, y + 42],
                    fill=(196, 122, 44))
        d.text((pad + 17, y + 8), badge, font=small, fill=(255, 250, 244))
    if n and total:
        tag = '%d / %d' % (n, total)
        d.text((W - pad - d.textlength(tag, font=small), pad - 6), tag,
               font=small, fill=(226, 222, 214))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    card.save(out_path, 'PNG')
    im = Image.open(out_path)
    if im.size != (W, H):
        return {'ok': False, 'reason': 'wrong_size', 'detail': str(im.size)}
    return {'ok': True, 'path': out_path, 'size': list(im.size),
            'bytes': os.path.getsize(out_path), 'sha256': sha256(out_path),
            'titleLines': len(tl), 'bodyLines': len(_wrap(d, body, mid, maxw)) if body else 0,
            'bodyTruncated': bool(body) and len(_wrap(d, body, mid, maxw)) > 6}
