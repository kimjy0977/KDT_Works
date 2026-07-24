// 이중언어 — 영어 기본, 한국어 토글. 서버는 쿠키 'lang'로 SSR 분기.
export type Lang = "en" | "ko";
export const DEFAULT_LANG: Lang = "en";

export function normalizeLang(v: string | undefined | null): Lang {
  return v === "ko" ? "ko" : "en";
}

// 콘텐츠 필드 선택: 영어면 en(비면 ko로 폴백), 아니면 ko
export function pick(lang: Lang, ko: string, en: string | null | undefined): string {
  if (lang === "en") return en && en.trim() ? en : ko;
  return ko;
}

// UI 문자열 사전 (서버·클라이언트 공용, 순수 데이터)
export const dict = {
  brandSub: { en: "Lineage of Inspiration", ko: "영감의 계보" },
  nav_archive: { en: "Archive", ko: "아카이브" },
  nav_essays: { en: "Essays", ko: "칼럼" },
  nav_board: { en: "Moodboard", ko: "무드보드" },
  nav_profile: { en: "Profile", ko: "프로필" },
  login: { en: "Sign in", ko: "로그인" },
  logout: { en: "Sign out", ko: "로그아웃" },

  // 홈
  home_eyebrow: { en: "Design Heritage Archive", ko: "디자인 원류 아카이브" },
  home_title_a: { en: "Mine new inspiration", ko: "오래된 뿌리에서," },
  home_title_b: { en: "from old roots", ko: "새로운 영감을" },
  home_lede: {
    en: "There's no shortage of places to be inspired by the new. ORIGIN walks the origins of design in chronological order, and an AI curator traces how each one echoes into today.",
    ko: "새로운 것에서 영감을 얻을 곳은 이미 넘친다. ORIGIN은 디자인이 태동한 원류를 시대순으로 따라가고, AI 큐레이터가 그 하나하나가 오늘로 어떻게 이어졌는지 짚어준다.",
  },
  meta_movements: { en: "movements", ko: "사조" },
  meta_works: { en: "origin works", ko: "원류 작품" },
  meta_lineage: { en: "of lineage", ko: "계보" },
  rail_foryou: { en: "For you", ko: "당신을 위한" },
  rail_foryou_sub: { en: "Ordered by the movements you follow", ko: "관심 사조를 먼저 보여드립니다" },
  rail_movements: { en: "Movements", ko: "사조" },
  rail_essays: { en: "Essays", ko: "칼럼" },
  browse_all: { en: "Browse the full archive →", ko: "전체 아카이브 보기 →" },
  read_essay: { en: "Read", ko: "읽기" },

  // 아카이브
  archive_title: { en: "The Archive", ko: "아카이브" },
  archive_eyebrow: { en: "Browse by movement", ko: "사조별 둘러보기" },
  filter_all: { en: "All", ko: "전체" },

  // 상세
  back_archive: { en: "← Back to archive", ko: "← 아카이브로" },
  detail_work: { en: "The work", ko: "작품" },
  detail_lineage: { en: "How it echoes today", ko: "오늘로 이어진 지점" },
  detail_source: { en: "Image source", ko: "이미지 출처" },
  detail_commons: { en: "Wikimedia Commons ↗", ko: "위키미디어 커먼즈 ↗" },
  save_add: { en: "♡ Save to moodboard", ko: "♡ 무드보드에 담기" },
  save_added: { en: "♥ Saved · remove", ko: "♥ 담김 · 빼기" },
  save_login: { en: "· sign in", ko: "· 로그인" },
  docent_title: { en: "✦ AI Curator — Docent", ko: "✦ AI 큐레이터 도슨트" },
  docent_load: { en: "Get commentary", ko: "해설 불러오기" },
  docent_regen: { en: "Regenerate", ko: "다시 생성" },
  docent_hint: {
    en: "The AI curator explains, like a docent, what this work started and how it reaches today's design.",
    ko: "이 작업이 시작한 것과, 오늘의 디자인으로 이어진 맥락을 AI가 도슨트처럼 풀어드립니다.",
  },
  docent_loading: { en: "Reading the lineage", ko: "큐레이터가 계보를 읽는 중" },
  docent_error: { en: "Couldn't load commentary. Check the AI key or try again.", ko: "해설을 불러오지 못했습니다. AI 키 설정을 확인하거나 다시 시도해 주세요." },
  related_works: { en: "More from this movement", ko: "이 사조의 다른 작품" },
  related_essays: { en: "Essays on this movement", ko: "이 사조를 다룬 칼럼" },

  // 무드보드
  board_eyebrow: { en: "My Moodboard", ko: "나의 무드보드" },
  board_title: { en: "My Moodboard", ko: "나의 무드보드" },
  board_login_prompt: { en: "Sign in to collect inspiration and get an AI taste summary.", ko: "로그인하면 영감을 모으고 AI 취향 요약을 받을 수 있습니다." },
  board_empty: { en: "You haven't saved any works yet.", ko: "아직 담은 작품이 없습니다." },
  board_empty_sub: { en: "Collect origins you love with the ♡ button in the archive.", ko: "아카이브에서 마음에 드는 원류를 ♡ 담기로 모아보세요." },
  board_browse: { en: "Browse the archive", ko: "아카이브 둘러보기" },
  note_placeholder: { en: "Note the inspiration you took…", ko: "이 작업에서 받은 영감을 메모…" },
  note_save: { en: "Save note", ko: "메모 저장" },
  note_saved: { en: "Saved", ko: "저장됨" },
  remove: { en: "Remove ✕", ko: "빼기 ✕" },
  taste_title: { en: "✦ AI Curator — Taste summary", ko: "✦ AI 큐레이터 — 취향 요약" },
  taste_run: { en: "Analyze my taste", ko: "내 취향 분석" },
  taste_regen: { en: "Re-analyze", ko: "다시 분석" },
  taste_loading: { en: "Reading your selections", ko: "선택을 해석하는 중" },
  taste_error: { en: "Analysis failed. Check the AI key or try again.", ko: "분석에 실패했습니다. AI 키 설정을 확인하거나 다시 시도해 주세요." },

  // 로그인
  auth_login: { en: "Sign in", ko: "로그인" },
  auth_signup: { en: "Create account", ko: "회원가입" },
  auth_sub: { en: "Sign in to collect inspiration on your moodboard and get AI curator summaries.", ko: "무드보드에 영감을 모으고, AI 큐레이터의 취향 요약을 받으려면 로그인하세요." },
  auth_email: { en: "Email", ko: "이메일" },
  auth_pw: { en: "Password", ko: "비밀번호" },
  auth_pw_hint: { en: "6+ characters", ko: "6자 이상" },
  auth_go_login: { en: "Sign in", ko: "로그인" },
  auth_go_signup: { en: "Sign up & start", ko: "가입하고 시작" },
  auth_processing: { en: "Working…", ko: "처리 중…" },
  auth_no_account: { en: "No account yet? ", ko: "계정이 없으신가요? " },
  auth_has_account: { en: "Already have an account? ", ko: "이미 계정이 있으신가요? " },

  // 온보딩
  wel_eyebrow: { en: "Welcome to ORIGIN", ko: "ORIGIN에 오신 것을 환영합니다" },
  wel_title: { en: "Tune your archive", ko: "당신의 아카이브를 맞춰보세요" },
  wel_sub: { en: "Two quick questions. We'll surface the roots you care about first — you can still browse everything.", ko: "간단한 두 질문. 관심 있는 뿌리를 먼저 보여드립니다 — 전부 그대로 탐색할 수 있어요." },
  wel_q1: { en: "Which movements pull you in?", ko: "어떤 사조에 끌리시나요?" },
  wel_q1_sub: { en: "Pick any number.", ko: "여러 개 골라도 됩니다." },
  wel_q2: { en: "What do you do?", ko: "어떤 일을 하시나요?" },
  wel_skip: { en: "Skip for now", ko: "지금은 건너뛰기" },
  wel_save: { en: "Save & explore", ko: "저장하고 시작" },
  role_graphic: { en: "Graphic designer", ko: "그래픽 디자이너" },
  role_product: { en: "Product / UX designer", ko: "프로덕트 · UX 디자이너" },
  role_student: { en: "Student", ko: "학생" },
  role_illustrator: { en: "Illustrator / Artist", ko: "일러스트레이터 · 작가" },
  role_curious: { en: "Just curious", ko: "그냥 관심 있어요" },

  // 프로필
  profile_title: { en: "Profile", ko: "프로필" },
  profile_interests: { en: "Your movements of interest", ko: "관심 사조" },
  profile_role: { en: "Your role", ko: "직군" },
  profile_save: { en: "Save changes", ko: "변경 저장" },
  profile_saved: { en: "Saved ✓", ko: "저장됨 ✓" },
} as const;

export type DictKey = keyof typeof dict;

export function t(lang: Lang, key: DictKey): string {
  return dict[key][lang];
}
