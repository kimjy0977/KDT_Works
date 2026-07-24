import Link from "next/link";
import { notFound } from "next/navigation";
import { getWorkFull } from "@/lib/queries";
import { createClient } from "@/lib/supabase/server";
import { getLang } from "@/lib/lang";
import { t, pick } from "@/lib/i18n";
import DocentPanel from "@/components/DocentPanel";
import SaveButton from "@/components/SaveButton";
import WorkCard from "@/components/WorkCard";
import EssayCard from "@/components/EssayCard";

export const dynamic = "force-dynamic";

export default async function WorkDetail({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const workId = Number(id);
  if (!Number.isFinite(workId)) notFound();

  const lang = await getLang();
  const full = await getWorkFull(workId);
  if (!full) notFound();
  const { work, related, essays } = full;

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  let initialSaved = false;
  if (user) {
    const { data } = await supabase
      .from("board_items")
      .select("id")
      .eq("user_id", user.id)
      .eq("work_id", workId)
      .maybeSingle();
    initialSaved = !!data;
  }

  const mvName = lang === "en" ? work.movement.name_en : work.movement.name_ko;

  return (
    <article className="detail wrap">
      <Link href="/archive" className="detail-back">
        {t(lang, "back_archive")}
      </Link>

      <div className="detail-grid">
        <figure className="detail-figure">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={work.image_url} alt={pick(lang, work.title, work.title_en)} />
          <figcaption className="detail-figcap">
            {t(lang, "detail_source")} ·{" "}
            <a href={work.source_url} target="_blank" rel="noreferrer">
              {t(lang, "detail_commons")}
            </a>
          </figcaption>
        </figure>

        <div className="detail-text">
          <div className="detail-era">
            {mvName} · {work.movement.era_start}–{work.movement.era_end}
          </div>
          <h1 className="detail-title">{pick(lang, work.title, work.title_en)}</h1>
          <p className="detail-byline">
            {work.creator} <span className="yr">· {work.year}</span>
          </p>

          <div className="detail-block">
            <h3>{t(lang, "detail_work")}</h3>
            <p>{pick(lang, work.description, work.description_en)}</p>
          </div>

          <div className="detail-block lineage">
            <h3>{t(lang, "detail_lineage")}</h3>
            <p>{pick(lang, work.lineage_note, work.lineage_en)}</p>
          </div>

          <div className="detail-actions">
            <SaveButton
              workId={work.id}
              initialSaved={initialSaved}
              isLoggedIn={!!user}
              lang={lang}
            />
          </div>

          <DocentPanel workId={work.id} lang={lang} />
        </div>
      </div>

      {essays.length > 0 && (
        <section className="related">
          <h2 className="related-head">{t(lang, "related_essays")}</h2>
          <div className="essay-grid">
            {essays.map((e) => (
              <EssayCard key={e.id} essay={e} lang={lang} />
            ))}
          </div>
        </section>
      )}

      {related.length > 0 && (
        <section className="related">
          <h2 className="related-head">{t(lang, "related_works")}</h2>
          <div className="grid">
            {related.map((w) => (
              <WorkCard key={w.id} work={w} lang={lang} />
            ))}
          </div>
        </section>
      )}
    </article>
  );
}
