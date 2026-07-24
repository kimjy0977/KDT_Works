// AI 큐레이터 — 무드보드 기반 취향 요약 (언어·직군 맞춤, 로그인 유저 본인)
import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { getLang } from "@/lib/lang";
import { anthropic, CURATOR_MODEL } from "@/lib/anthropic";
import { rolePhrase } from "@/lib/curator";
import { allow } from "@/lib/ratelimit";

type Row = {
  note: string | null;
  work: {
    title: string;
    title_en: string;
    creator: string;
    year: string;
    movement: { name_ko: string; name_en: string };
  };
};

export async function POST() {
  if (!process.env.ANTHROPIC_API_KEY) {
    return NextResponse.json({ error: "AI 키 미설정" }, { status: 503 });
  }

  const lang = await getLang();
  const ko = lang === "ko";
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  // 유저당 분당 5회 제한 (Claude 비용 방어)
  if (!allow(`taste:${user.id}`, 5, 60_000)) {
    return NextResponse.json({ error: "요청이 너무 많습니다. 잠시 후 다시." }, { status: 429 });
  }

  const [{ data: boardData }, { data: prof }] = await Promise.all([
    supabase
      .from("board_items")
      .select(
        "note, work:works(title, title_en, creator, year, movement:movements(name_ko, name_en))"
      )
      .eq("user_id", user.id)
      .order("created_at", { ascending: false }),
    supabase.from("profiles").select("role").eq("id", user.id).maybeSingle(),
  ]);

  const items = (boardData ?? []) as unknown as Row[];
  if (items.length === 0) {
    return NextResponse.json({ error: "empty board" }, { status: 400 });
  }

  const rp = rolePhrase(prof?.role ?? null, lang);
  const list = items
    .map((it) => {
      const w = it.work;
      const title = ko ? w.title : w.title_en || w.title;
      const mv = ko ? w.movement.name_ko : w.movement.name_en;
      const note = it.note ? (ko ? ` — 메모: ${it.note}` : ` — note: ${it.note}`) : "";
      return `- ${title} / ${w.creator} (${w.year}) · ${mv}${note}`;
    })
    .join("\n");

  const prompt = ko
    ? `당신은 디자인 큐레이터입니다. ${rp}가 '영감 아카이브'에서 무드보드에 담은 원류 작업 목록입니다. 이 선택을 읽고 취향을 짚어주세요.

[담은 작업 ${items.length}점]
${list}

요구사항: 한국어 존댓말, 3개 문단(빈 줄 구분).
1문단: 이 선택들을 관통하는 취향/계열을 한두 문장으로 규정.
2문단: 왜 그렇게 보이는지 담은 작업들을 근거로 설명.
3문단: 그 취향을 ${rp}의 오늘 작업에 활용하는 구체적 방향 + 다음에 탐구하면 좋을 사조/작가 1~2개 추천.
억지 칭찬 금지, 관찰 근거로. 각 문단 3~4문장.`
    : `You are a design curator. Below is the list of origin works ${rp} saved to a moodboard in an "inspiration archive." Read the selection and name their taste.

[Saved works: ${items.length}]
${list}

Requirements: English, 3 paragraphs (blank-line separated).
P1: name the taste/lineage running through these picks in a sentence or two.
P2: explain why, grounded in the specific saved works.
P3: a concrete way ${rp} can use this taste in today's work + 1–2 movements/designers to explore next.
No empty praise — ground it in observation. 3–4 sentences each.`;

  try {
    const msg = await anthropic.messages.create({
      model: CURATOR_MODEL,
      max_tokens: 800,
      messages: [{ role: "user", content: prompt }],
    });
    const text = msg.content
      .filter((b) => b.type === "text")
      .map((b) => (b as { text: string }).text)
      .join("\n");
    return NextResponse.json({ text });
  } catch (e) {
    const m = e instanceof Error ? e.message : "AI error";
    return NextResponse.json({ error: m }, { status: 500 });
  }
}
