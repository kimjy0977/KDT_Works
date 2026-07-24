import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { getLang } from "@/lib/lang";
import { t } from "@/lib/i18n";
import type { BoardEntry } from "@/lib/types";
import BoardList from "@/components/BoardList";
import TasteSummary from "@/components/TasteSummary";

export const dynamic = "force-dynamic";

export default async function BoardPage() {
  const lang = await getLang();
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return (
      <div className="wrap empty">
        <p style={{ fontFamily: "var(--serif)", fontSize: "1.6rem" }}>
          {t(lang, "board_title")}
        </p>
        <p>{t(lang, "board_login_prompt")}</p>
        <p style={{ marginTop: "1.4rem" }}>
          <Link className="btn btn-solid" href="/login?next=/board">
            {t(lang, "login")}
          </Link>
        </p>
      </div>
    );
  }

  const { data } = await supabase
    .from("board_items")
    .select("*, work:works(*, movement:movements(*))")
    .eq("user_id", user.id)
    .order("created_at", { ascending: false });

  const items = (data ?? []) as BoardEntry[];

  return (
    <div className="wrap">
      <div className="page-head">
        <p className="eyebrow">{t(lang, "board_eyebrow")}</p>
        <h1>{t(lang, "board_title")}</h1>
      </div>

      {items.length === 0 ? (
        <div className="empty">
          <p>{t(lang, "board_empty")}</p>
          <p style={{ fontSize: "0.9rem" }}>{t(lang, "board_empty_sub")}</p>
          <p style={{ marginTop: "1.2rem" }}>
            <Link className="btn" href="/archive">
              {t(lang, "board_browse")}
            </Link>
          </p>
        </div>
      ) : (
        <>
          <TasteSummary count={items.length} lang={lang} />
          <BoardList items={items} lang={lang} />
        </>
      )}
    </div>
  );
}
