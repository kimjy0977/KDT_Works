// 간단한 인메모리 rate limit + 응답 캐시.
// ⚠️ 서버리스는 인스턴스별 메모리라 warm 인스턴스 기준 best-effort (완벽한 전역 제한 아님).
//    비용 폭주 1차 방어용. 엄격한 제한이 필요하면 Upstash/Redis 등 외부 스토어 권장.

const hits = new Map<string, number[]>();

/** key에 대해 windowMs 안에서 limit회까지 허용. 초과면 false. */
export function allow(key: string, limit: number, windowMs: number): boolean {
  const now = Date.now();
  const arr = (hits.get(key) ?? []).filter((t) => now - t < windowMs);
  if (arr.length >= limit) {
    hits.set(key, arr);
    return false;
  }
  arr.push(now);
  hits.set(key, arr);
  return true;
}

const cache = new Map<string, { text: string; at: number }>();
const CACHE_TTL = 1000 * 60 * 60 * 24; // 24h

export function getCache(key: string): string | null {
  const c = cache.get(key);
  if (c && Date.now() - c.at < CACHE_TTL) return c.text;
  return null;
}
export function setCache(key: string, text: string): void {
  cache.set(key, { text, at: Date.now() });
}

/** 요청 IP 추출 (프록시 헤더 우선) */
export function clientIp(req: Request): string {
  return (
    req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
    req.headers.get("x-real-ip") ||
    "unknown"
  );
}
