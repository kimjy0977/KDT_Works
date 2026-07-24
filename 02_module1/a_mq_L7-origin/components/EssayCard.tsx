import Link from "next/link";
import { pick, type Lang } from "@/lib/i18n";
import type { Essay } from "@/lib/types";

export default function EssayCard({
  essay,
  lang,
}: {
  essay: Essay;
  lang: Lang;
}) {
  return (
    <Link href={`/essays/${essay.slug}`} className="essay-card">
      <div className="essay-card-frame">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={essay.hero_url}
          alt={pick(lang, essay.title_ko, essay.title_en)}
          loading="lazy"
        />
      </div>
      <div className="essay-card-body">
        <span className="eyebrow">{lang === "en" ? "Essay" : "칼럼"}</span>
        <h3>{pick(lang, essay.title_ko, essay.title_en)}</h3>
        <p>{pick(lang, essay.dek_ko, essay.dek_en)}</p>
      </div>
    </Link>
  );
}
