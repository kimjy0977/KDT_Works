/* verify-ui.mjs — 화면이 «실제로 도는지» 브라우저 밖에서 잰다.
 *
 * ★왜 필요한가
 *   디자인을 갈아엎으면 «보기에는» 멀쩡한데 선택자 하나가 어긋나 기능이 죽는다.
 *   스크린샷은 그걸 못 잡는다 — 안 보이는 것은 안 보이니까.
 *   ⇒ ①HTML 이 약속한 ID 가 다 있는가 ②ui.js 가 «찾는» 선택자가 HTML·CSS 에 있는가
 *     ③CSS 가 «쓰는» 토큰이 :root 에 정의돼 있는가 를 파일에서 대조한다.
 *
 * 쓰는 법:  node tools/verify-ui.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => readFileSync(join(ROOT, p), 'utf8');

let pass = 0, fail = 0;
const ok = (name, cond, detail = '') => {
  if (cond) { pass++; console.log(`  ok   ${name}${detail ? ' — ' + detail : ''}`); }
  else { fail++; console.log(`  FAIL ${name}${detail ? ' — ' + detail : ''}`); }
};

const html = read('index.html');
const ui = read('app/ui.js');
const css = read('app/style.css');

console.log('='.repeat(62));
console.log('화면 검증 — 「보이는 것」이 아니라 「도는 것」');
console.log('='.repeat(62));

// ── ① ui.js 가 «찾는» ID 가 HTML 에 있는가 ────────────────────
console.log('\n■ 1. ui.js 가 찾는 ID 가 HTML 에 있는가');
const wantIds = [...new Set([...ui.matchAll(/\$\('#([A-Za-z][\w-]*)'\)/g)].map((m) => m[1]))];
// ★ui.js 가 «직접 만드는» ID 도 있다 (모드 설정칸·전시 입력칸).
//   그건 HTML 에 없는 게 «맞다». 검사기가 그걸 못 가리면 정상 코드에 벌을 준다.
//   실측 2026-09-10 — cfgModel·cfgHost·cfgKey·exTitle·exStmt 를 「없다」고 올렸다.
const madeIds = new Set([...ui.matchAll(/id="([A-Za-z][\w-]*)"/g)].map((m) => m[1]));
const missIds = wantIds.filter((id) => !html.includes(`id="${id}"`) && !madeIds.has(id));
ok(`ID ${wantIds.length}개 전부 닿음`, missIds.length === 0,
  missIds.length ? '없는 것: ' + missIds.join(', ')
    : `HTML ${wantIds.length - madeIds.size > 0 ? wantIds.filter((i) => html.includes(`id="${i}"`)).length : 0}개 · ui.js 가 만드는 것 ${wantIds.filter((i) => madeIds.has(i)).length}개`);

// ── ② ui.js 가 «만드는» 클래스가 CSS 에 있는가 ─────────────────
console.log('\n■ 2. ui.js 가 붙이는 클래스에 스타일이 있는가');
//   el(tag, '클래스', …) 와 class="…" 양쪽에서 뽑는다
const fromEl = [...ui.matchAll(/\bel\(\s*'[a-z]+'\s*,\s*'([^']+)'/g)].map((m) => m[1]);
const fromAttr = [...ui.matchAll(/class="([^"$]+)"/g)].map((m) => m[1]);
const classes = [...new Set(
  [...fromEl, ...fromAttr].flatMap((c) => c.split(/\s+/)).filter((c) => c && !c.includes('$')),
)];
const noStyle = classes.filter((c) => !css.includes('.' + c));
ok(`클래스 ${classes.length}종 전부 스타일 있음`, noStyle.length === 0,
  noStyle.length ? '스타일 없는 것: ' + noStyle.join(', ') : '');

// ── ③ CSS 가 «쓰는» 토큰이 정의돼 있는가 ───────────────────────
console.log('\n■ 3. CSS 가 쓰는 토큰이 :root 에 정의돼 있는가');
const used = [...new Set([...css.matchAll(/var\((--[\w-]+)\)/g)].map((m) => m[1]))];
// ★한 줄에 토큰이 여럿 있다 (--bg:#FAFAFA; --surface:#FFFFFF; …).
//   줄머리에 고정하면 «첫 개만» 잡고 나머지를 「정의 없음」으로 올린다 (실측).
const defined = new Set([...css.matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1]));
const undef = used.filter((v) => !defined.has(v));
ok(`토큰 ${used.length}종 전부 정의됨`, undef.length === 0,
  undef.length ? '정의 없는 것: ' + undef.join(', ') : '');

// ui.js 가 인라인으로 쓰는 토큰도 — 여기가 잘 빠진다
const uiVars = [...new Set([...ui.matchAll(/var\((--[\w-]+)\)/g)].map((m) => m[1]))];
const uiUndef = uiVars.filter((v) => !defined.has(v));
ok(`ui.js 인라인 토큰 ${uiVars.length}종 정의됨`, uiUndef.length === 0,
  uiUndef.length ? '★' + uiUndef.join(', ') : uiVars.join(' ') || '없음');

// ── ④ 다크모드에서도 «같은 토큰»이 다 재정의되는가 ──────────────
console.log('\n■ 4. 다크모드가 토큰을 빠짐없이 덮는가');
const lightBlock = css.slice(css.indexOf(':root{'), css.indexOf('@media (prefers-color-scheme: dark)'));
const darkBlock = css.slice(css.indexOf('@media (prefers-color-scheme: dark)'),
  css.indexOf(':root[data-theme="dark"]'));
const lightTok = [...lightBlock.matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1]);
const darkTok = new Set([...darkBlock.matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1]));
//   색이 아닌 것(간격·반경·모션)은 다크에서 안 바꿔도 된다
const COLORISH = /^--(bg|surface|card|ink|dim|faint|line|control|accent|ok|warn|bad|code|e[123])/;
const darkMiss = lightTok.filter((t) => COLORISH.test(t) && !darkTok.has(t) && t !== '--card');
ok(`색 토큰이 다크에서 전부 재정의됨`, darkMiss.length === 0,
  darkMiss.length ? '★안 바뀌는 것: ' + darkMiss.join(', ') : `${darkTok.size}종`);

// ── ⑤ 접근성 규약 ────────────────────────────────────────────
console.log('\n■ 5. 접근성 — DESIGN.md 에서 정한 것');
ok('focus-visible 링이 있다', /:focus-visible\s*\{[^}]*outline\s*:\s*2px/.test(css));
ok('outline:none 으로 지운 곳이 없다', !/outline\s*:\s*none/.test(css));
ok('prefers-reduced-motion 을 존중한다', css.includes('prefers-reduced-motion'));
ok('한국어 줄바꿈(keep-all)이 있다', css.includes('word-break:keep-all'));
const minH = [...css.matchAll(/min-height\s*:\s*(\d+)px/g)].map((m) => +m[1]);
ok('버튼·입력 최소 높이 44px 이상', minH.filter((h) => h >= 44).length >= 3,
  '44+ 인 규칙 ' + minH.filter((h) => h >= 44).length + '개');
ok('서체를 «정했다» (시스템 폰트 의존 아님)', css.includes('Noto Sans KR'));

// ── ⑥ 타입 스케일이 «뒤집히지» 않았는가 ────────────────────────
console.log('\n■ 6. 타입 스케일 — 제목이 본문보다 큰가');
const bodySize = +(css.match(/body\{[\s\S]*?font-size:\s*([\d.]+)px/) || [])[1];
const h2Size = +(css.match(/\bh2\{[^}]*font-size:\s*([\d.]+)px/) || [])[1];
const h3Size = +(css.match(/\bh3\{[^}]*font-size:\s*([\d.]+)px/) || [])[1];
ok('h2 > 본문', h2Size > bodySize, `h2 ${h2Size} > body ${bodySize}`);
ok('h3 ≥ 본문', h3Size >= bodySize, `h3 ${h3Size} ≥ body ${bodySize}`);

// ── ⑦ 화면과 코드가 «같은 말»을 쓰는가 ─────────────────────────
console.log('\n■ 7. 화면이 코드와 같은 말을 쓰는가');
const agent = read('app/agent.js');
const phaseLabels = [...agent.matchAll(/label:\s*'([^']+)'/g)].map((m) => m[1]);
const inHero = phaseLabels.filter((l) => html.includes(`<b>${l}</b>`));
ok('히어로 흐름이 PHASES 와 같은 이름을 쓴다',
  inHero.length >= 5, `${inHero.length}/${phaseLabels.length} 일치 — ${inHero.join(' ')}`);

// ── ⑧ ★부르는데 «없는» 함수가 있는가 ──────────────────────────
//   실측 2026-09-10 — renderHistory 를 다시 쓰면서 «그 아래 있던» loadEval 을
//   통째로 지웠다. 구문 검사(node --check)는 통과한다 — 부를 때야 터진다.
//   ⇒ 「부르는 이름」과 「정의된 이름」을 대조한다.
console.log('\n■ 8. 부르는데 정의가 «없는» 함수');
const definedFns = new Set([
  // 줄머리 함수 · 즉시실행 함수 «둘 다» 잡는다.
  //   실측 — (async function boot(){…})() 를 「정의 없음」으로 올렸다.
  ...[...ui.matchAll(/(?:async )?function (\w+)/g)].map((m) => m[1]),
  ...[...ui.matchAll(/(?:const|let) (\w+) *= *(?:async )?[(\w]/g)].map((m) => m[1]),
  ...[...ui.matchAll(/^import \{([^}]+)\}/gm)].flatMap((m) => m[1].split(',').map((x) => x.trim())),
  ...[...ui.matchAll(/(?:const|let) (\w+)/g)].map((m) => m[1]),
]);
const GLOBAL = new Set(['fetch','alert','confirm','prompt','setTimeout','clearTimeout','Blob','URL',
  'JSON','Object','Array','Math','Date','String','Number','Boolean','Set','Map','Promise','console',
  'document','window','navigator','localStorage','if','for','while','switch','catch','return','function',
  'typeof','new','await','el','esc','summary','saveRun','loadRuns','goTab','replay','estimateCost',
  'parseInt','parseFloat','isNaN','encodeURIComponent','decodeURIComponent','history','location',
  // ★키워드는 «함수 호출»이 아니다. 정규식이 이름처럼 잡아 낸다.
  'async','var','else','do','try','of','in']);
const called = [...new Set([...ui.matchAll(/(?<![.\w$])([a-z][A-Za-z0-9_]{2,})\s*\(/g)].map((m) => m[1]))];
const ghosts = called.filter((c) => !definedFns.has(c) && !GLOBAL.has(c));
ok(`부르는 함수 ${called.length}개 전부 정의됨`, ghosts.length === 0,
  ghosts.length ? '★정의 없음: ' + ghosts.join(', ') : '');

// ── ⑨ 하드코딩된 색이 남아 있지 않은가 ─────────────────────────
console.log('\n■ 8. 색을 컴포넌트에 직접 쓰지 않았는가');
const body = css.slice(css.indexOf('/* ── 바탕'));
const hard = [...body.matchAll(/#[0-9A-Fa-f]{6}\b/g)].map((m) => m[0]);
ok('토큰 밖에 하드코딩 색이 없다', hard.length === 0,
  hard.length ? '★' + [...new Set(hard)].join(', ') : '');

// ── ⑨ ★DESIGN.md 가 말한 브레이크포인트가 CSS 에 «실제로» 있는가 ──
//   실측 2026-09-10 — §7 에 720·860 을 적었는데 CSS 에 없는 숫자였다.
//   머리로 「대충 이쯤」 하고 적으면 문서가 코드를 지어낸다.
console.log('\n■ 9. 문서가 말한 브레이크포인트가 CSS 에 있는가');
const design = read('DESIGN.md');
const sec7 = design.slice(design.indexOf('## 7. 레이아웃'), design.indexOf('## 8.'));
// ★«@media 안»의 숫자만 브레이크포인트다.
//   그냥 (min|max)-width 를 다 잡으면 .wrap 의 max-width:1160px 같은
//   «컨테이너 폭»까지 브레이크포인트로 오인한다 (실측으로 걸렸다).
const claimed = [...new Set([...sec7.matchAll(/@media[^)]*?(?:min|max)-width:\s*(\d+)px/g)].map((m) => m[1]))];
const realBp = new Set([...css.matchAll(/@media[^{]*?(?:min|max)-width:\s*(\d+)px/g)].map((m) => m[1]));
const invented = claimed.filter((b) => !realBp.has(b));
ok(`문서의 브레이크포인트 ${claimed.length}개가 CSS 에 있음`, invented.length === 0,
  invented.length ? '★CSS 에 없는 숫자: ' + invented.join(', ') + 'px'
    : '실제 ' + [...realBp].sort((a, b) => a - b).join(' / ') + 'px');

console.log('\n' + '='.repeat(62));
console.log(`통과 ${pass} · 실패 ${fail}`);
process.exit(fail ? 1 : 0);
