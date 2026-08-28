// 안내 화면이 쓰는 작품 목록. 챗봇이 다루는 범위를 방문자가 먼저 읽도록 둔다.
// 청크 스키마(id·text·url·section·vector)와는 별개다 — 검색·프롬프트 파이프라인은 건드리지 않는다.
// 썸네일은 MYTH GALLERY 원본을 그대로 가리킨다 (12/12 · 합계 421KB, 2026-08-29 확인).

export type Work = {
  slug: string; url: string; title: string;
  artist: string; era: string; chunks: number;
};

export const THUMB = (slug: string) =>
  `https://myth-gallery.vercel.app/img/works/thumb/${slug}.webp`;

export const WORKS: Work[] = [
  {
    slug: "greek-0a50eec5ef",
    url: "https://myth-gallery.vercel.app/ko/greek/works/greek-0a50eec5ef",
    title: "헤라클레스와 켄타우로스 네소스",
    artist: "잠볼로냐",
    era: "르네상스 1400년~1600년",
    chunks: 4,
  },
  {
    slug: "greek-2be2a8a891",
    url: "https://myth-gallery.vercel.app/ko/greek/works/greek-2be2a8a891",
    title: "아폴론과 다프네",
    artist: "안토니오 델 폴라이올로",
    era: "르네상스 1400년~1600년",
    chunks: 4,
  },
  {
    slug: "greek-22ddc6d999",
    url: "https://myth-gallery.vercel.app/ko/greek/works/greek-22ddc6d999",
    title: "페르가몬 제단 동쪽 프리즈 — 아테나, 알퀴오네우스, 가이아, 니케",
    artist: "익명",
    era: "고대 기원전 700년~기원후 400년",
    chunks: 4,
  },
  {
    slug: "greek-35001919e7",
    url: "https://myth-gallery.vercel.app/ko/greek/works/greek-35001919e7",
    title: "케이론과 아킬레우스",
    artist: "존 싱어 사전트",
    era: "근현대 1900년~",
    chunks: 4,
  },
  {
    slug: "greek-199855cc84",
    url: "https://myth-gallery.vercel.app/ko/greek/works/greek-199855cc84",
    title: "마르스와 미네르바의 싸움 (아테나가 아레스를 쓰러뜨림 — 아프로디테 동반)",
    artist: "조제프 브누아 쉬베",
    era: "신고전주의 1750년~1830년",
    chunks: 4,
  },
  {
    slug: "greek-17b732695d",
    url: "https://myth-gallery.vercel.app/ko/greek/works/greek-17b732695d",
    title: "큐피드와 프시케",
    artist: "안토니 반 다이크",
    era: "바로크 1600년~1750년",
    chunks: 4,
  },
  {
    slug: "greek-4612f58e9a",
    url: "https://myth-gallery.vercel.app/ko/greek/works/greek-4612f58e9a",
    title: "아폴론과 디아나",
    artist: "알브레히트 뒤러",
    era: "르네상스 1400년~1600년",
    chunks: 4,
  },
  {
    slug: "greek-2a03908f61",
    url: "https://myth-gallery.vercel.app/ko/greek/works/greek-2a03908f61",
    title: "피그말리온과 갈라테이아",
    artist: "에티엔 모리스 팔코네",
    era: "신고전주의 1750년~1830년",
    chunks: 4,
  },
  {
    slug: "greek-09374e014c",
    url: "https://myth-gallery.vercel.app/ko/greek/works/greek-09374e014c",
    title: "유피테르, 메르쿠리우스, 비르투스",
    artist: "도소 도시",
    era: "르네상스 1400년~1600년",
    chunks: 3,
  },
  {
    slug: "greek-1713af792f",
    url: "https://myth-gallery.vercel.app/ko/greek/works/greek-1713af792f",
    title: "오디세우스와 폴리페모스",
    artist: "아르놀트 뵈클린",
    era: "19세기 후반 1850년~1910년",
    chunks: 2,
  },
  {
    slug: "greek-0da6452d3a",
    url: "https://myth-gallery.vercel.app/ko/greek/works/greek-0da6452d3a",
    title: "오로라와 케팔로스",
    artist: "프랑수아 부셰",
    era: "신고전주의 1750년~1830년",
    chunks: 2,
  },
  {
    slug: "greek-011d6bf12a",
    url: "https://myth-gallery.vercel.app/ko/greek/works/greek-011d6bf12a",
    title: "프로세르피나의 납치",
    artist: "페테르 파울 루벤스",
    era: "바로크 1600년~1750년",
    chunks: 2,
  },
];

// 아카이브 전체 규모. 이 챗봇이 다루는 것은 이 중 그리스·로마 12점뿐이다.
export const MYTHS = [
  { name: "그리스·로마", works: 469, covered: true },
  { name: "힌두", works: 120, covered: false },
  { name: "북유럽", works: 117, covered: false },
  { name: "중국", works: 113, covered: false },
  { name: "이집트", works: 92, covered: false },
  { name: "메소포타미아", works: 71, covered: false },
];
