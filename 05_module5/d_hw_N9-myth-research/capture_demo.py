# -*- coding: utf-8 -*-
"""★데모 화면을 «사람 손 없이» 찍는다 — docs/demo.png

왜 스크립트로 만드나
  ① 공개 저장소에 올라가는 이미지라 **개인 정보가 찍히면 안 된다.**
     손으로 찍었을 때 두 번이나 탭 그룹·북마크바가 들어가 지웠다.
     ⇒ 빈 프로필 + 헤드리스면 브라우저 UI 자체가 «없다».
  ② ★화면이 바뀌면 캡처도 바뀌어야 한다. 손으로 찍으면 안 다시 찍는다.
     실사고 2026-09-22 — 사이드바 문구를 고쳤는데 캡처엔 옛 문구가 남았다.
     ⇒ 한 줄로 다시 찍을 수 있으면 다시 찍는다.
  ③ 「어떻게 찍었나」를 «글»이 아니라 «코드»로 남긴다.

쓰는 법
  streamlit run app.py --server.port 8512     (먼저 띄워 둔다)
  python capture_demo.py                      (docs/demo.png 로 저장)
  python capture_demo.py --port 8511 --out docs/other.png

의존성 — websockets 만 쓴다 (CDP 를 직접 말한다). chrome 은 설치된 것을 찾는다.
"""
import argparse
import asyncio
import base64
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = [
    r"C:/Program Files/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
]
# 캡처할 질문 — 4홉이 이 프로젝트의 «하는 일»이라 4홉을 찍는다.
QUESTION = '서로 만난 적 없는 문명들이 왜 닮은 이야기를 남겼는가 — 창조·홍수·저승·영웅 네 축으로 본다'
READY_MARK = "도면에서 읽히는 것"          # 이 글자가 뜨면 보고서가 다 그려진 것이다


def find_chrome():
    for p in CHROME:
        if os.path.exists(p):
            return p
    p = shutil.which("chrome") or shutil.which("msedge")
    if p:
        return p
    raise SystemExit("★chrome 을 못 찾았습니다")


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    n = s.getsockname()[1]
    s.close()
    return n


def wait_devtools(port, secs=20):
    end = time.time() + secs
    while time.time() < end:
        try:
            with urllib.request.urlopen(
                    "http://127.0.0.1:%d/json/version" % port, timeout=1) as r:
                return json.load(r)["webSocketDebuggerUrl"]
        except Exception:
            time.sleep(0.3)
    raise SystemExit("★DevTools 가 안 열렸습니다")


async def shoot(ws_url, url, out, w, h, wait_s):
    import websockets
    nid = [0]

    async with websockets.connect(ws_url, max_size=64 * 1024 * 1024) as ws:
        async def cmd(method, **params):
            nid[0] += 1
            me = nid[0]
            await ws.send(json.dumps({"id": me, "method": method,
                                      "params": params}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == me:
                    if "error" in msg:
                        raise SystemExit("★CDP %s: %s" % (method, msg["error"]))
                    return msg.get("result", {})

        # 브라우저 대상에 붙어 «페이지» 하나를 잡는다
        targets = (await cmd("Target.getTargets"))["targetInfos"]
        page = next(t for t in targets if t["type"] == "page")
        sid = (await cmd("Target.attachToTarget",
                         targetId=page["targetId"], flatten=True))["sessionId"]

        async def pcmd(method, **params):
            nid[0] += 1
            me = nid[0]
            await ws.send(json.dumps({"id": me, "method": method,
                                      "params": params, "sessionId": sid}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == me:
                    if "error" in msg:
                        raise SystemExit("★CDP %s: %s" % (method, msg["error"]))
                    return msg.get("result", {})

        await pcmd("Page.enable")
        await pcmd("Runtime.enable")
        await pcmd("Emulation.setDeviceMetricsOverride",
                   width=w, height=h, deviceScaleFactor=1, mobile=False)
        await pcmd("Page.navigate", url=url)

        # ★답이 다 그려질 때까지 «본다». 고정 sleep 을 쓰지 않는다 —
        #   LLM 호출 시간이 매번 다르고, 짧으면 빈 화면을 찍는다.
        end = time.time() + wait_s
        seen = False
        while time.time() < end:
            r = await pcmd("Runtime.evaluate",
                           expression="document.body ? document.body.innerText"
                                      " : ''", returnByValue=True)
            txt = (r.get("result") or {}).get("value") or ""
            if READY_MARK in txt:
                seen = True
                await asyncio.sleep(1.2)          # 표가 다 그려지도록 한 박자
                break
            await asyncio.sleep(0.5)
        if not seen:
            raise SystemExit("★%d초 안에 「%s」가 안 떴습니다 — 서버가 떠 있습니까?"
                             % (wait_s, READY_MARK))

        shot = await pcmd("Page.captureScreenshot", format="png")
        raw = base64.b64decode(shot["data"])
        io.open(out, "wb").write(raw)
        return len(raw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8523)
    ap.add_argument("--out", default=os.path.join(HERE, "docs/demo.png"))
    ap.add_argument("--width", type=int, default=1680)
    ap.add_argument("--height", type=int, default=1180)
    ap.add_argument("--axis", default="주제")
    ap.add_argument("--wait", type=int, default=90)
    a = ap.parse_args()

    url = ("http://localhost:%d/?auto=1&axis=%s&q=%s"
           % (a.port, urllib.parse.quote(a.axis), urllib.parse.quote(QUESTION)))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)

    # ★빈 프로필 — 북마크·탭·확장·줌이 «없는» 곳에서 연다.
    prof = tempfile.mkdtemp(prefix="kdt-shot-")
    chrome = find_chrome()
    dport = free_port()
    proc = subprocess.Popen(
        [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         "--no-first-run", "--no-default-browser-check",
         "--remote-debugging-port=%d" % dport,
         "--user-data-dir=" + prof,
         "--window-size=%d,%d" % (a.width, a.height), "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ws_url = wait_devtools(dport)
        n = asyncio.run(shoot(ws_url, url, a.out, a.width, a.height, a.wait))
        print("  OK %s · %d bytes · %dx%d" % (a.out, n, a.width, a.height))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        shutil.rmtree(prof, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
