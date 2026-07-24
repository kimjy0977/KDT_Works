import Link from "next/link";
import { getArchive, getFeaturedEssays, getMyProfile } from "@/lib/queries";
import { getLang } from "@/lib/lang";
import { t } from "@/lib/i18n";
import WorkCard from "@/components/WorkCard";
import EssayCard from "@/components/EssayCard";

export const dynamic = "force-dynamic";

export default async function Home() {
  const lang = await getLang();
  const [archive, featured, profile] = await Promise.all([
    getArchive(),
    getFeaturedEssays(3),
    getMyProfile(),
  ]);

  const hasData = archive.length > 0;
  const totalWorks = archive.reduce((n, m) => n + m.works.length, 0);
  const eraFrom = hasData ? Math.min(...archive.map((m) => m.era_start)) : 0;
  const eraTo = hasData ? Math.max(...archive.map((m) => m.era_end)) : 0;

  const slugById = new Map(archive.map((m) => [m.id, m.slug]));
  const interests = profile?.interests ?? [];
  const allWorks = archive.flatMap((m) => m.works);
  const forYou =
    interests.length > 0
      ? allWorks
          .filter((w) => interests.includes(slugById.get(w.movement_id) ?? ""))
          .slice(0, 8)
      : archive.map((m) => m.works[0]).filter(Boolean).slice(0, 8);

  return (
    <>
      <section className="hero wrap">
        <p className="eyebrow">{t(lang, "home_eyebrow")}</p>
        <h1 className="hero-title">
          {t(lang, "home_title_a")}
          <br />
          <em>{t(lang, "home_title_b")}</em>
        </h1>
        <p className="hero-lede">{t(lang, "home_lede")}</p>
        {hasData && (
          <div className="hero-meta">
            <span>
              <b>{archive.length}</b> {t(lang, "meta_movements")}
            </span>
            <span>
              <b>{totalWorks}</b> {t(lang, "meta_works")}
            </span>
            <span>
              <b>
                {eraFrom}–{eraTo}
              </b>{" "}
              {t(lang, "meta_lineage")}
            </span>
          </div>
        )}
      </section>

      {!hasData && (
        <div className="wrap empty">
          <p>{lang === "en" ? "The archive is empty." : "아직 아카이브가 비어 있습니다."}</p>
          <p style={{ fontSize: "0.85rem" }}>
            {lang === "en"
              ? "Run schema.sql · seed.sql on Supabase to fill it."
              : "Supabase에 schema.sql · seed.sql을 실행하면 채워집니다."}
          </p>
        </div>
      )}

      {hasData && (
        <div className="wrap">
          {/* For you */}
          <section className="rail">
            <div className="rail-head">
              <div>
                <h2 className="rail-title">{t(lang, "rail_foryou")}</h2>
                <p className="rail-sub">
                  {interests.length > 0
                    ? t(lang, "rail_foryou_sub")
                    : lang === "en"
                    ? "One landmark from each movement to start."
                    : "각 사조의 대표작으로 시작해 보세요."}
                </p>
              </div>
              <Link href="/welcome" className="rail-link">
                {lang === "en" ? "Personalize →" : "맞춤 설정 →"}
              </Link>
            </div>
            <div className="grid">
              {forYou.map((w) => (
                <WorkCard key={w.id} work={w} lang={lang} />
              ))}
            </div>
          </section>

          {/* Movements */}
          <section className="rail">
            <div className="rail-head">
              <h2 className="rail-title">{t(lang, "rail_movements")}</h2>
              <Link href="/archive" className="rail-link">
                {t(lang, "browse_all")}
              </Link>
            </div>
            <div className="tile-grid">
              {archive.map((m) => (
                <Link href={`/archive#${m.slug}`} className="mv-tile" key={m.id}>
                  <div className="mv-tile-frame">
                    {m.works[0] && (
                      /* eslint-disable-next-line @next/next/no-img-element */
                      <img src={m.works[0].image_url} alt="" loading="lazy" />
                    )}
                  </div>
                  <div className="mv-tile-body">
                    <span className="mv-era">
                      {m.era_start}–{m.era_end}
                    </span>
                    <h3>{lang === "en" ? m.name_en : m.name_ko}</h3>
                  </div>
                </Link>
              ))}
            </div>
          </section>

          {/* Essays */}
          {featured.length > 0 && (
            <section className="rail">
              <div className="rail-head">
                <h2 className="rail-title">{t(lang, "rail_essays")}</h2>
                <Link href="/essays" className="rail-link">
                  {lang === "en" ? "All essays →" : "칼럼 전체 →"}
                </Link>
              </div>
              <div className="essay-grid">
                {featured.map((e) => (
                  <EssayCard key={e.id} essay={e} lang={lang} />
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </>
  );
}
