/* ================================================================
   tts.js · 강의노트 부분 듣기 (Web Speech API · 바닐라 · 자체완결)
   - 문단/블록별 ▶ 칩 · 강 전체 듣기 · 선택영역 읽기
   - 일시정지/재개 · 다시듣기 · 속도 · 한국어 음성 폴백
   - 디자인: 에디토리얼 톤(액센트 #CE1225, Pretendard, 헤어라인, 칩형)
   - 결정 근거: 브리지 KBMT-20260727-2 (매니저 GO)
   ================================================================ */
(function () {
  "use strict";
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return; // 미지원=조용히 폴백
  var synth = window.speechSynthesis;

  /* ---- 상태 ---- */
  var rate = 1;                 // 재생 속도(다음 발화부터 적용)
  var koVoice = null;           // 한국어 음성
  var hasKo = false;
  var lastText = "";            // 다시듣기용
  var activeChip = null;        // 현재 재생 칩(하이라이트)

  function pickVoice() {
    var vs = synth.getVoices() || [];
    koVoice = null;
    for (var i = 0; i < vs.length; i++) {
      if (/^ko\b|ko[-_]/i.test(vs[i].lang)) { koVoice = vs[i]; break; }
    }
    hasKo = !!koVoice;
  }
  pickVoice();
  if (typeof synth.onvoiceschanged !== "undefined") synth.onvoiceschanged = pickVoice;

  /* ---- 텍스트 정리 ---- */
  function clean(t) { return (t || "").replace(/\s+/g, " ").trim(); }

  /* ---- 발화 ---- */
  function stopAll() {
    try { synth.cancel(); } catch (e) {}
    setActive(null);
    hidePlayer();
  }
  function speak(text) {
    text = clean(text);
    if (!text) return;
    try { synth.cancel(); } catch (e) {}
    lastText = text;
    var u = new SpeechSynthesisUtterance(text);
    u.lang = "ko-KR";
    if (koVoice) u.voice = koVoice;
    u.rate = rate;
    u.onend = function () { setActive(null); hidePlayer(); };
    u.onerror = function () { setActive(null); hidePlayer(); };
    synth.speak(u);
    showPlayer();
    if (!hasKo) notifyOnce();
  }

  function setActive(chip) {
    if (activeChip && activeChip.classList) activeChip.classList.remove("tts-on");
    activeChip = chip;
    if (chip && chip.classList) chip.classList.add("tts-on");
  }

  /* ---- 미니 플레이어(고정) ---- */
  var player = null, ppBtn = null;
  function buildPlayer() {
    player = document.createElement("div");
    player.className = "tts-player";
    player.setAttribute("aria-hidden", "true");
    player.innerHTML =
      '<button type="button" data-a="pp" title="일시정지/재개">⏸</button>' +
      '<button type="button" data-a="replay" title="다시 듣기">↺</button>' +
      '<button type="button" data-a="stop" title="정지">■</button>' +
      '<label class="tts-rate">속도' +
        '<select data-a="rate">' +
          '<option value="0.75">0.75×</option>' +
          '<option value="1" selected>1×</option>' +
          '<option value="1.25">1.25×</option>' +
          '<option value="1.5">1.5×</option>' +
        '</select></label>';
    document.body.appendChild(player);
    ppBtn = player.querySelector('[data-a="pp"]');
    player.addEventListener("click", function (e) {
      var b = e.target.closest("button"); if (!b) return;
      var a = b.getAttribute("data-a");
      if (a === "pp") {
        if (synth.paused) { synth.resume(); ppBtn.textContent = "⏸"; }
        else { synth.pause(); ppBtn.textContent = "▶"; }
      } else if (a === "replay") {
        if (lastText) speak(lastText);
      } else if (a === "stop") {
        stopAll();
      }
    });
    player.querySelector('[data-a="rate"]').addEventListener("change", function (e) {
      rate = parseFloat(e.target.value) || 1;
      if (lastText && (synth.speaking || synth.paused)) speak(lastText); // 즉시 반영
    });
  }
  function showPlayer() { if (player) { player.classList.add("tts-show"); ppBtn.textContent = "⏸"; player.setAttribute("aria-hidden", "false"); } }
  function hidePlayer() { if (player && !synth.speaking && !synth.paused) { player.classList.remove("tts-show"); player.setAttribute("aria-hidden", "true"); } }

  /* ---- 안내(음성 없음) ---- */
  var notified = false;
  function notifyOnce() {
    if (notified) return; notified = true;
    var n = document.createElement("div");
    n.className = "tts-note";
    n.textContent = "이 브라우저에 한국어 음성이 없어 기본 음성으로 읽습니다. (Chrome·Edge·Safari 권장)";
    document.body.appendChild(n);
    setTimeout(function () { n.classList.add("tts-fade"); }, 4500);
    setTimeout(function () { if (n.parentNode) n.parentNode.removeChild(n); }, 5600);
  }

  /* ---- 칩 만들기 ---- */
  function chip(label, title) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "tts-chip";
    b.setAttribute("aria-label", title || "듣기");
    b.title = title || "듣기";
    b.innerHTML = '<span aria-hidden="true">▶</span>' + (label ? '<i>' + label + '</i>' : '');
    return b;
  }

  /* ---- 부착 ---- */
  function attach() {
    var secs = document.querySelectorAll("main .section");
    Array.prototype.forEach.call(secs, function (sec) {
      // 강 전체 듣기 (섹션 상단, h2 바로 뒤)
      var h2 = sec.querySelector("h2");
      var secText = clean(sec.textContent);
      if (h2 && secText) {
        var bar = document.createElement("div");
        bar.className = "tts-secbar";
        var whole = chip("이 강 전체 듣기", "이 강 전체를 소리로 듣기");
        whole.classList.add("tts-whole");
        whole.addEventListener("click", function () { setActive(whole); speak(secText); });
        bar.appendChild(whole);
        if (h2.nextSibling) h2.parentNode.insertBefore(bar, h2.nextSibling);
        else h2.parentNode.appendChild(bar);
      }
      // 블록별 ▶ (문단·콜아웃만 — 줄/목록 단위는 "선택 읽기"로 충분, 칩 과밀 방지)
      var blocks = sec.querySelectorAll(":scope > p, :scope > .notice");
      Array.prototype.forEach.call(blocks, function (el) {
        if (el.classList && el.classList.contains("tts-secbar")) return;
        var txt = clean(el.textContent);
        if (!txt || txt.length < 2) return;
        var c = chip("", "이 부분 듣기");
        c.classList.add("tts-inline");
        c.addEventListener("click", function () { setActive(c); speak(txt); });
        el.appendChild(document.createTextNode(" "));
        el.appendChild(c);
      });
    });
  }

  /* ---- 선택영역 읽기(플로팅) ---- */
  var selBtn = null;
  function buildSelBtn() {
    selBtn = document.createElement("button");
    selBtn.type = "button";
    selBtn.className = "tts-sel";
    selBtn.textContent = "🔊 선택 읽기";
    selBtn.style.display = "none";
    selBtn.addEventListener("mousedown", function (e) { e.preventDefault(); });
    selBtn.addEventListener("click", function () {
      var s = window.getSelection ? String(window.getSelection()) : "";
      if (clean(s)) { setActive(null); speak(s); }
      hideSel();
    });
    document.body.appendChild(selBtn);
  }
  function hideSel() { if (selBtn) selBtn.style.display = "none"; }
  function onSel() {
    if (!selBtn) return;
    var s = window.getSelection && window.getSelection();
    var txt = s ? clean(String(s)) : "";
    if (!txt || txt.length < 2 || !s.rangeCount) { hideSel(); return; }
    var r = s.getRangeAt(0).getBoundingClientRect();
    if (!r || (!r.width && !r.height)) { hideSel(); return; }
    selBtn.style.display = "block";
    var top = r.top + window.scrollY - 42;
    var left = r.left + window.scrollX + (r.width / 2) - 48;
    selBtn.style.top = Math.max(8, top) + "px";
    selBtn.style.left = Math.max(8, left) + "px";
  }

  /* ---- CSS 주입(페이지 변수 재사용) ---- */
  function injectCSS() {
    var css =
      ".tts-chip{display:inline-flex;align-items:center;gap:.3em;vertical-align:baseline;" +
      "margin-left:.4em;padding:.05em .5em;border:1px solid var(--line,#e2ddd3);border-radius:999px;" +
      "background:var(--surface,#fff);color:var(--ink-3,#8B8578);font-family:var(--sans,system-ui);" +
      "font-size:.7rem;line-height:1.5;cursor:pointer;transition:all .12s;user-select:none;-webkit-user-select:none}" +
      ".tts-chip:hover{border-color:var(--brand,#CE1225);color:var(--brand,#CE1225)}" +
      ".tts-chip i{font-style:normal;font-weight:600;letter-spacing:.01em}" +
      ".tts-chip.tts-on{background:var(--brand,#CE1225);border-color:var(--brand,#CE1225);color:#fff}" +
      ".tts-secbar{margin:.1rem 0 .9rem}" +
      ".tts-chip.tts-whole{font-size:.74rem;padding:.22em .8em;color:var(--brand-ink,#9E0E1C);border-color:var(--brand,#CE1225)}" +
      ".tts-chip.tts-whole:hover{background:var(--brand-soft,#FBE7E8)}" +
      ".tts-chip.tts-inline{opacity:.6}" +
      ".tts-chip.tts-inline:hover,.tts-chip.tts-inline.tts-on{opacity:1}" +
      ".tts-player{position:fixed;right:18px;bottom:18px;z-index:9999;display:none;align-items:center;gap:6px;" +
      "padding:8px 10px;background:var(--ink,#1A1813);border-radius:12px;box-shadow:0 6px 24px rgba(0,0,0,.28);" +
      "font-family:var(--sans,system-ui)}" +
      ".tts-player.tts-show{display:flex}" +
      ".tts-player button{border:0;background:transparent;color:#fff;font-size:1rem;cursor:pointer;" +
      "width:30px;height:30px;border-radius:8px;line-height:1}" +
      ".tts-player button:hover{background:rgba(255,255,255,.15)}" +
      ".tts-rate{color:#cfc9bd;font-size:.72rem;display:flex;align-items:center;gap:4px;margin-left:2px}" +
      ".tts-rate select{background:#2a2620;color:#fff;border:1px solid #4a443a;border-radius:6px;font-size:.72rem;padding:2px 4px}" +
      ".tts-sel{position:absolute;z-index:10000;padding:6px 11px;border:0;border-radius:999px;" +
      "background:var(--brand,#CE1225);color:#fff;font-family:var(--sans,system-ui);font-size:.76rem;font-weight:600;" +
      "cursor:pointer;box-shadow:0 4px 14px rgba(206,18,37,.4)}" +
      ".tts-note{position:fixed;left:50%;bottom:20px;transform:translateX(-50%);z-index:10001;max-width:90vw;" +
      "padding:10px 14px;background:var(--ink,#1A1813);color:#fff;border-radius:10px;font-family:var(--sans,system-ui);" +
      "font-size:.8rem;line-height:1.5;transition:opacity .8s}" +
      ".tts-note.tts-fade{opacity:0}" +
      "@media(max-width:640px){.tts-player{right:10px;bottom:10px}.tts-chip{font-size:.66rem}}" +
      "@media print{.tts-chip,.tts-player,.tts-sel,.tts-secbar{display:none!important}}";
    var st = document.createElement("style");
    st.setAttribute("data-tts", "1");
    st.appendChild(document.createTextNode(css));
    document.head.appendChild(st);
  }

  /* ---- 초기화 ---- */
  function init() {
    injectCSS();
    buildPlayer();
    buildSelBtn();
    attach();
    document.addEventListener("mouseup", function () { setTimeout(onSel, 10); });
    document.addEventListener("selectionchange", function () {
      var s = window.getSelection && window.getSelection();
      if (!s || !clean(String(s))) hideSel();
    });
    window.addEventListener("beforeunload", function () { try { synth.cancel(); } catch (e) {} });
    // 페이지 이탈/해시 전환 시 정지
    window.addEventListener("hashchange", stopAll);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
