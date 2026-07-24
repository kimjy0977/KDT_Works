// 무드보드 CRUD API — 로그인 유저 본인 데이터만 (RLS로 이중 방어)
import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

function parseWorkId(v: unknown): number | null {
  const n = Number(v);
  return Number.isInteger(n) && n > 0 ? n : null;
}

async function requireUser() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  return { supabase, user };
}

// 담기
export async function POST(req: Request) {
  const { supabase, user } = await requireUser();
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const body = await req.json().catch(() => ({}));
  const workId = parseWorkId(body.workId);
  if (!workId) return NextResponse.json({ error: "invalid workId" }, { status: 400 });

  const { error } = await supabase
    .from("a_mq_origin_board_items")
    .upsert(
      { user_id: user.id, work_id: workId },
      { onConflict: "user_id,work_id", ignoreDuplicates: true }
    );
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}

// 메모 수정
export async function PATCH(req: Request) {
  const { supabase, user } = await requireUser();
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const body = await req.json().catch(() => ({}));
  const workId = parseWorkId(body.workId);
  if (!workId) return NextResponse.json({ error: "invalid workId" }, { status: 400 });
  const note = typeof body.note === "string" ? body.note.slice(0, 2000) : null;

  const { error } = await supabase
    .from("a_mq_origin_board_items")
    .update({ note })
    .eq("user_id", user.id)
    .eq("work_id", workId);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}

// 빼기
export async function DELETE(req: Request) {
  const { supabase, user } = await requireUser();
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const body = await req.json().catch(() => ({}));
  const workId = parseWorkId(body.workId);
  if (!workId) return NextResponse.json({ error: "invalid workId" }, { status: 400 });

  const { error } = await supabase
    .from("a_mq_origin_board_items")
    .delete()
    .eq("user_id", user.id)
    .eq("work_id", workId);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}
