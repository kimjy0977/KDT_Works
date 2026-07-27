/* ================================================================
   listen.js · 듣기 전용 오디오 플레이어 (읽기/듣기 분리)
   - 로봇 Web Speech TTS 폐기(음질 미흡) → 듣기 = 사전생성 자연음성 MP3.
   - 읽기 전용 = 강의노트 본문(그대로). 듣기 전용 = 강의톤 나레이션 오디오.
   - 사용법: <section class="section" data-audio="audio/n9-1.mp3"> → 플레이어 렌더.
             data-audio 없이 data-listen="soon" → "준비 중" 자리표시.
   - 디자인: 에디토리얼 톤(액센트 #CE1225·헤어라인·칩). 결정 근거: 브리지 B안.
   ================================================================ */
(function () {
  "use strict";

  function injectCSS() {
    var css =
      ".listen-bar{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:.25rem 0 1.1rem;" +
      "padding:11px 14px;border:1px solid var(--line,#E5E1D6);border-left:3px solid var(--brand,#CE1225);" +
      "border-radius:8px;background:var(--surface,#fff)}" +
      ".listen-lab{font-family:var(--sans,system-ui);font-size:.72rem;font-weight:800;letter-spacing:.06em;" +
      "text-transform:uppercase;color:var(--brand,#CE1225);white-space:nowrap}" +
      ".listen-soon{font-size:.82rem;color:var(--ink-3,#8C8579);line-height:1.4}" +
      ".listen-soon i{font-style:normal;opacity:.75}" +
      ".listen-audio{height:36px;flex:1;min-width:220px;max-width:540px}" +
      "@media print{.listen-bar{display:none!important}}";
    var st = document.createElement("style");
    st.setAttribute("data-listen", "1");
    st.appendChild(document.createTextNode(css));
    document.head.appendChild(st);
  }

  function makeBar(sec) {
    var audio = sec.getAttribute("data-audio");
    var soon = sec.getAttribute("data-listen") === "soon";
    if (!audio && !soon) return null;
    var bar = document.createElement("div");
    bar.className = "listen-bar";
    if (audio) {
      bar.innerHTML =
        '<span class="listen-lab">🎧 듣기 버전</span>' +
        '<audio class="listen-audio" controls preload="none" src="' + audio + '"></audio>';
    } else {
      bar.innerHTML =
        '<span class="listen-lab">🎧 듣기 버전</span>' +
        '<span class="listen-soon">자연 음성 나레이션 <b>준비 중</b> <i>— 강의톤 대본을 자연 음성 오디오로 추가 예정</i></span>';
    }
    return bar;
  }

  function attach() {
    var secs = document.querySelectorAll("main .section[data-audio], main .section[data-listen]");
    Array.prototype.forEach.call(secs, function (sec) {
      var bar = makeBar(sec);
      if (!bar) return;
      var h2 = sec.querySelector("h2");
      if (h2 && h2.nextSibling) h2.parentNode.insertBefore(bar, h2.nextSibling);
      else if (h2) h2.parentNode.appendChild(bar);
      else sec.insertBefore(bar, sec.firstChild);
    });
  }

  function init() { injectCSS(); attach(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
