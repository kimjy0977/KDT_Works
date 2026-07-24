"use client";

// 상태 없이 CSS로 아이콘 전환 (setState-in-effect 회피 · 하이드레이션 안전)
export default function ThemeToggle() {
  function toggle() {
    const isDark =
      document.documentElement.getAttribute("data-theme") === "dark";
    const next = isDark ? "light" : "dark";
    if (next === "dark") document.documentElement.setAttribute("data-theme", "dark");
    else document.documentElement.removeAttribute("data-theme");
    try {
      localStorage.setItem("theme", next);
    } catch {}
  }

  return (
    <button className="icon-btn theme-toggle" onClick={toggle} aria-label="테마 전환" title="Light / Dark">
      <span className="to-dark">☾</span>
      <span className="to-light">☀</span>
    </button>
  );
}
