// 서버 측 데이터 조회 (서버 컴포넌트에서 사용)
import { createClient } from "@/lib/supabase/server";
import type {
  Movement,
  Work,
  WorkWithMovement,
  Essay,
  Profile,
} from "@/lib/types";

export type MovementWithWorks = Movement & { works: Work[] };

// 아카이브 전체: 사조(정렬순) + 각 사조의 작품
export async function getArchive(): Promise<MovementWithWorks[]> {
  const supabase = await createClient();
  const [{ data: movements }, { data: works }] = await Promise.all([
    supabase.from("movements").select("*").order("sort"),
    supabase.from("works").select("*").order("id"),
  ]);

  return (movements ?? []).map((m: Movement) => ({
    ...m,
    works: (works ?? []).filter((w: Work) => w.movement_id === m.id),
  }));
}

// 작품 하나 + 소속 사조 + 관련 작품 + 관련 칼럼
export async function getWorkFull(id: number): Promise<{
  work: WorkWithMovement;
  related: Work[];
  essays: Essay[];
} | null> {
  const supabase = await createClient();
  const { data } = await supabase
    .from("works")
    .select("*, movement:movements(*)")
    .eq("id", id)
    .single();
  const work = data as WorkWithMovement | null;
  if (!work) return null;

  const [{ data: related }, { data: essays }] = await Promise.all([
    supabase
      .from("works")
      .select("*")
      .eq("movement_id", work.movement_id)
      .neq("id", work.id)
      .order("id")
      .limit(6),
    supabase
      .from("essays")
      .select("*")
      .eq("movement_slug", work.movement.slug)
      .order("sort"),
  ]);

  return {
    work,
    related: (related ?? []) as Work[],
    essays: (essays ?? []) as Essay[],
  };
}

export async function getEssays(): Promise<Essay[]> {
  const supabase = await createClient();
  const { data } = await supabase.from("essays").select("*").order("sort");
  return (data ?? []) as Essay[];
}

export async function getFeaturedEssays(limit = 3): Promise<Essay[]> {
  const supabase = await createClient();
  const { data } = await supabase
    .from("essays")
    .select("*")
    .eq("featured", true)
    .order("sort")
    .limit(limit);
  return (data ?? []) as Essay[];
}

export async function getEssay(slug: string): Promise<Essay | null> {
  const supabase = await createClient();
  const { data } = await supabase
    .from("essays")
    .select("*")
    .eq("slug", slug)
    .single();
  return (data as Essay) ?? null;
}

// 여러 작품을 id로 (칼럼 본문 임베드용)
export async function getWorksByIds(ids: number[]): Promise<Work[]> {
  if (ids.length === 0) return [];
  const supabase = await createClient();
  const { data } = await supabase.from("works").select("*").in("id", ids);
  return (data ?? []) as Work[];
}

// 현재 유저 프로필 (없으면 null)
export async function getMyProfile(): Promise<Profile | null> {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return null;
  const { data } = await supabase
    .from("profiles")
    .select("*")
    .eq("id", user.id)
    .maybeSingle();
  return (data as Profile) ?? null;
}
