import LoginForm from "@/components/LoginForm";
import { getLang } from "@/lib/lang";

// 오픈 리다이렉트 방지: 내부 상대경로(`/...`)만 허용, 그 외엔 /board
function safeNext(next?: string): string {
  if (
    next &&
    next.startsWith("/") &&
    !next.startsWith("//") &&
    !next.startsWith("/\\")
  ) {
    return next;
  }
  return "/board";
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const { next } = await searchParams;
  const lang = await getLang();
  return <LoginForm next={safeNext(next)} lang={lang} />;
}
