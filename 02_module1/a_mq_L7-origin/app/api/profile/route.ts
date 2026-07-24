// 프로필(온보딩 맞춤) 저장 — 본인 것만
import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function POST(req: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const body = await req.json().catch(() => ({}));
  const interests = Array.isArray(body.interests)
    ? body.interests.filter((x: unknown) => typeof x === "string").slice(0, 20)
    : [];
  const role = typeof body.role === "string" ? body.role.slice(0, 40) : null;

  const { error } = await supabase.from("a_mq_origin_profiles").upsert(
    {
      id: user.id,
      interests,
      role,
      onboarded_at: new Date().toISOString(),
    },
    { onConflict: "id" }
  );
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}
