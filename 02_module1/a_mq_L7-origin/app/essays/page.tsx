import { getEssays } from "@/lib/queries";
import { getLang } from "@/lib/lang";
import { t } from "@/lib/i18n";
import EssayCard from "@/components/EssayCard";

export const dynamic = "force-dynamic";

export default async function EssaysPage() {
  const lang = await getLang();
  const essays = await getEssays();

  return (
    <div className="wrap">
      <div className="page-head">
        <p className="eyebrow">{lang === "en" ? "Columns on the origins" : "원류를 읽는 칼럼"}</p>
        <h1>{t(lang, "nav_essays")}</h1>
      </div>

      {essays.length === 0 ? (
        <div className="empty">
          <p>{lang === "en" ? "No essays yet." : "아직 칼럼이 없습니다."}</p>
        </div>
      ) : (
        <div className="essay-grid" style={{ paddingBottom: "3rem" }}>
          {essays.map((e) => (
            <EssayCard key={e.id} essay={e} lang={lang} />
          ))}
        </div>
      )}
    </div>
  );
}
