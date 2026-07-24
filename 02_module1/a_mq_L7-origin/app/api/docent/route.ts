// AI 큐레이터 — 작품 도슨트 해설 (언어·직군 맞춤, 서버에서만 키 사용)
// 비용 보호: (작품·언어·직군)별 캐시 + Claude 호출에 IP rate limit.
import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { getLang } from "@/lib/lang";
import { anthropic, CURATOR_MODEL } from "@/lib/anthropic";
import { rolePhrase } from "@/lib/curator";
import { allow, getCache, setCache, clientIp } from "@/lib/ratelimit";
import type { WorkWithMovement } from "@/lib/types";

export async function POST(req: Request) {
  if (!process.env.ANTHROPIC_API_KEY) {
    return NextResponse.json({ error: "AI 키 미설정" }, { status: 503 });
  }

  const body = await req.json().catch(() => ({}));
  const workId = Number(body.workId);
  if (!Number.isInteger(workId)) {
    return NextResponse.json({ error: "invalid workId" }, { status: 400 });
  }

  const lang = await getLang();
  const supabase = await createClient();

  const [{ data: workData }, { data: userData }] = await Promise.all([
    supabase.from("a_mq_origin_works").select("*, movement:a_mq_origin_movements(*)").eq("id", workId).single(),
    supabase.auth.getUser(),
  ]);
  const work = workData as WorkWithMovement | null;
  if (!work) return NextResponse.json({ error: "not found" }, { status: 404 });

  // 로그인 유저의 직군(있으면 말투 맞춤)
  let role: string | null = null;
  if (userData.user) {
    const { data: prof } = await supabase
      .from("a_mq_origin_profiles")
      .select("role")
      .eq("id", userData.user.id)
      .maybeSingle();
    role = prof?.role ?? null;
  }

  // 캐시 히트 → Claude 호출 없이 즉시 반환 (비용 0)
  const cacheKey = `docent:${workId}:${lang}:${role ?? "none"}`;
  const cached = getCache(cacheKey);
  if (cached) return NextResponse.json({ text: cached, cached: true });

  // Claude 호출은 IP당 분당 8회로 제한 (남용·비용 방어)
  if (!allow(`docent:${clientIp(req)}`, 8, 60_000)) {
    return NextResponse.json({ error: "요청이 너무 많습니다. 잠시 후 다시." }, { status: 429 });
  }

  const ko = lang === "ko";
  const rp = rolePhrase(role, lang);
  const title = ko ? work.title : work.title_en || work.title;
  const mv = ko ? work.movement.name_ko : work.movement.name_en;
  const desc = ko ? work.description : work.description_en || work.description;

  const prompt = ko
    ? `당신은 디자인사 전문 도슨트입니다. 아래 작품을 ${rp}에게 들려주듯 해설하세요.

[작품] ${title} — ${work.creator} (${work.year})
[사조] ${mv} (${work.movement.era_start}–${work.movement.era_end})
[작품 설명] ${desc}

요구사항: 한국어 존댓말, 3개 문단(빈 줄 구분).
1문단: 이 작업이 당대에 처음 시도하거나 깨뜨린 것 — 왜 원류인지.
2문단: 그 감각이 오늘의 디자인(UI·그래픽·브랜딩·프로덕트)으로 이어진 지점을 구체적으로.
3문단: ${rp}의 시선에서 지금 훔쳐갈 만한 영감 한 가지 — 실천적 조언.
각 문단 3~4문장. 과장·미사여구 대신 밀도 있게.`
    : `You are an expert design-history docent. Explain the work below as if speaking to ${rp}.

[Work] ${title} — ${work.creator} (${work.year})
[Movement] ${mv} (${work.movement.era_start}–${work.movement.era_end})
[Description] ${desc}

Requirements: English, 3 paragraphs (blank-line separated).
P1: what this work first attempted or broke in its time — why it is an origin.
P2: concretely, how that sensibility reaches today's design (UI, graphics, branding, product).
P3: one piece of inspiration ${rp} could steal from it now — practical advice.
3–4 sentences each. Dense, not flowery.`;

  try {
    const msg = await anthropic.messages.create({
      model: CURATOR_MODEL,
      max_tokens: 700,
      messages: [{ role: "user", content: prompt }],
    });
    const text = msg.content
      .filter((b) => b.type === "text")
      .map((b) => (b as { text: string }).text)
      .join("\n");
    setCache(cacheKey, text);
    return NextResponse.json({ text });
  } catch (e) {
    const m = e instanceof Error ? e.message : "AI error";
    return NextResponse.json({ error: m }, { status: 500 });
  }
}
