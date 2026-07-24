import Link from "next/link";
import { notFound } from "next/navigation";
import { getEssay, getWorksByIds } from "@/lib/queries";
import { getLang } from "@/lib/lang";
import { pick } from "@/lib/i18n";
import WorkCard from "@/components/WorkCard";
import type { Work } from "@/lib/types";

export const dynamic = "force-dynamic";

const WORK_TOKEN = /^\[\[work:(\d+)\]\]$/;

export default async function EssayDetail({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const lang = await getLang();
  const essay = await getEssay(slug);
  if (!essay) notFound();

  const body = pick(lang, essay.body_ko, essay.body_en);
  const blocks = body
    .split(/\n\n+/)
    .map((b) => b.trim())
    .filter(Boolean);

  // 임베드된 작품 id 모아서 한 번에 조회
  const ids = blocks
    .map((b) => b.match(WORK_TOKEN))
    .filter((m): m is RegExpMatchArray => !!m)
    .map((m) => Number(m[1]));
  const works = await getWorksByIds(ids);
  const byId = new Map<number, Work>(works.map((w) => [w.id, w]));

  return (
    <article className="essay-article">
      <div className="essay-hero">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={essay.hero_url} alt="" />
      </div>
      <div className="wrap-narrow">
        <Link href="/essays" className="detail-back">
          {lang === "en" ? "← All essays" : "← 칼럼 전체"}
        </Link>
        <p className="eyebrow" style={{ marginTop: "1.4rem" }}>
          {lang === "en" ? "Essay" : "칼럼"}
        </p>
        <h1 className="essay-title">{pick(lang, essay.title_ko, essay.title_en)}</h1>
        <p className="essay-dek">{pick(lang, essay.dek_ko, essay.dek_en)}</p>

        <div className="essay-body">
          {blocks.map((b, i) => {
            const m = b.match(WORK_TOKEN);
            if (m) {
              const w = byId.get(Number(m[1]));
              if (!w) return null;
              return (
                <div className="essay-embed" key={i}>
                  <WorkCard work={w} lang={lang} />
                </div>
              );
            }
            return <p key={i}>{b}</p>;
          })}
        </div>
      </div>
    </article>
  );
}
