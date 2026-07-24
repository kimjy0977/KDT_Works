import type { Lang } from "@/lib/i18n";

export default function SiteFooter({ lang }: { lang: Lang }) {
  const en = lang === "en";
  return (
    <footer className="footer">
      <div className="footer-inner">
        <span className="fb">
          {en
            ? "ORIGIN — mine new inspiration from old roots."
            : "ORIGIN — 오래된 뿌리에서, 새로운 영감을."}
        </span>
        <span>
          {en
            ? "Images · Wikimedia Commons (public domain / CC) · educational project · KDT AI Agent course"
            : "이미지 · 위키미디어 커먼즈 (퍼블릭 도메인 / CC) · 교육용 프로젝트 · KDT AI 에이전트 과정"}
        </span>
      </div>
    </footer>
  );
}
