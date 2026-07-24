import Link from "next/link";
import { pick, type Lang } from "@/lib/i18n";
import type { Work } from "@/lib/types";

export default function WorkCard({
  work,
  lang,
  index,
  search,
}: {
  work: Work;
  lang: Lang;
  index?: number;
  search?: string;
}) {
  const title = pick(lang, work.title, work.title_en);
  return (
    <Link
      href={`/works/${work.id}`}
      className="card"
      data-search={search ? search.toLowerCase() : undefined}
    >
      <div className="card-frame">
        {index != null && (
          <span className="card-index">{String(index).padStart(2, "0")}</span>
        )}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={work.image_url} alt={title} loading="lazy" />
      </div>
      <div className="card-body">
        <div className="card-title">{title}</div>
        <div className="card-meta">
          {work.creator} · {work.year}
        </div>
      </div>
    </Link>
  );
}
