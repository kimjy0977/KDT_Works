// AI 큐레이터 프롬프트용 — 직군을 자연스러운 표현으로 (언어별)
import type { Lang } from "@/lib/i18n";

const MAP: Record<string, { en: string; ko: string }> = {
  graphic: { en: "a graphic designer", ko: "그래픽 디자이너" },
  product: { en: "a product/UX designer", ko: "프로덕트·UX 디자이너" },
  student: { en: "a design student", ko: "디자인을 배우는 학생" },
  illustrator: { en: "an illustrator", ko: "일러스트레이터" },
  curious: { en: "a curious newcomer to design", ko: "디자인에 갓 관심 갖는 사람" },
};

const FALLBACK = {
  en: "a curious visitor",
  ko: "디자인의 뿌리를 탐구하는 사람",
};

export function rolePhrase(role: string | null, lang: Lang): string {
  const e = role && MAP[role] ? MAP[role] : FALLBACK;
  return lang === "ko" ? e.ko : e.en;
}
