// 서버 전용 — 쿠키에서 현재 언어를 읽는다 (기본 en)
import { cookies } from "next/headers";
import { normalizeLang, type Lang } from "./i18n";

export async function getLang(): Promise<Lang> {
  const c = await cookies();
  return normalizeLang(c.get("lang")?.value);
}
