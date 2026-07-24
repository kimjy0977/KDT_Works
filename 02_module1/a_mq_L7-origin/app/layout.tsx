import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Masthead from "@/components/Masthead";
import SiteFooter from "@/components/SiteFooter";
import { getLang } from "@/lib/lang";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ORIGIN — Lineage of Inspiration",
  description:
    "Mine new inspiration from old roots. A design-history archive where an AI curator traces how the origins of design echo into today.",
};

// 초기 페인트 전에 저장된 테마 적용 (플래시 방지) — 기본 라이트
const themeScript = `(function(){try{if(localStorage.getItem('theme')==='dark'){document.documentElement.setAttribute('data-theme','dark');}}catch(e){}})();`;

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const lang = await getLang();
  return (
    <html lang={lang} className={inter.variable}>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        {/* Pretendard — 한글+라틴 모던 고딕 (본문·제목 공용) */}
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css"
        />
      </head>
      <body>
        <Masthead lang={lang} />
        <main className="site-main">{children}</main>
        <SiteFooter lang={lang} />
      </body>
    </html>
  );
}
