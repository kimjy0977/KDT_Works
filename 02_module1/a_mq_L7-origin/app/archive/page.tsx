import { getArchive, getMyProfile } from "@/lib/queries";
import { getLang } from "@/lib/lang";
import { t } from "@/lib/i18n";
import WorkCard from "@/components/WorkCard";
import LineageTimeline from "@/components/LineageTimeline";
import ArchiveSearch from "@/components/ArchiveSearch";

export const dynamic = "force-dynamic";

export default async function ArchivePage() {
  const lang = await getLang();
  const [archive, profile] = await Promise.all([getArchive(), getMyProfile()]);
  const interests = profile?.interests ?? [];

  // 관심 사조를 먼저, 나머지는 sort 순
  const ordered = [...archive].sort((a, b) => {
    const ai = interests.includes(a.slug) ? 0 : 1;
    const bi = interests.includes(b.slug) ? 0 : 1;
    return ai - bi || a.sort - b.sort;
  });

  // 사조별 글로벌 시작 인덱스 (렌더 중 변수 재할당 회피)
  const starts = ordered.map((_, i) =>
    ordered.slice(0, i).reduce((s, mm) => s + mm.works.length, 0)
  );

  return (
    <div className="wrap">
      <div className="page-head">
        <p className="eyebrow">{t(lang, "archive_eyebrow")}</p>
        <h1>{t(lang, "archive_title")}</h1>
      </div>

      <LineageTimeline movements={ordered} lang={lang} />

      <ArchiveSearch lang={lang} />

      <p id="archive-empty" className="archive-empty" style={{ display: "none" }}>
        {lang === "en" ? "No works match your search." : "검색 결과가 없습니다."}
      </p>

      {ordered.map((m, mi) => (
        <section className="movement" key={m.id} id={m.slug}>
          <div className="movement-head">
            <span className="movement-era">
              {m.era_start} — {m.era_end}
              {interests.includes(m.slug) && (
                <span className="foryou-tag">
                  {lang === "en" ? "For you" : "관심"}
                </span>
              )}
            </span>
            <h2 className="movement-name">
              {lang === "en" ? m.name_en : m.name_ko}
              <span className="en">
                {lang === "en" ? m.name_ko : m.name_en}
              </span>
            </h2>
            <p className="movement-blurb">
              {lang === "en" ? m.blurb_en || m.blurb : m.blurb}
            </p>
          </div>

          <div className="grid">
            {m.works.map((w, wi) => (
              <WorkCard
                key={w.id}
                work={w}
                lang={lang}
                index={starts[mi] + wi + 1}
                search={`${w.title} ${w.title_en} ${w.creator} ${w.year} ${m.name_ko} ${m.name_en}`}
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
