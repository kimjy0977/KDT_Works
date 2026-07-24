// ORIGIN 공용 타입 — DB 테이블과 1:1 대응

export type Movement = {
  id: number;
  slug: string;
  name_ko: string;
  name_en: string;
  era_start: number;
  era_end: number;
  blurb: string;
  blurb_en: string;
  sort: number;
};

export type Work = {
  id: number;
  movement_id: number;
  title: string;
  title_en: string;
  creator: string;
  year: string;
  image_url: string;
  source_url: string;
  description: string;
  description_en: string;
  lineage_note: string;
  lineage_en: string;
};

// 조인 결과: 작품 + 소속 사조
export type WorkWithMovement = Work & { movement: Movement };

export type Essay = {
  id: number;
  slug: string;
  title_ko: string;
  title_en: string;
  dek_ko: string;
  dek_en: string;
  body_ko: string;
  body_en: string;
  hero_url: string;
  movement_slug: string | null;
  featured: boolean;
  sort: number;
};

export type Profile = {
  id: string;
  interests: string[];
  role: string | null;
  onboarded_at: string | null;
};

export type BoardItem = {
  id: number;
  user_id: string;
  work_id: number;
  note: string | null;
  is_public: boolean;
  created_at: string;
};

// 무드보드 화면용: 담은 항목 + 작품 정보
export type BoardEntry = BoardItem & { work: WorkWithMovement };
