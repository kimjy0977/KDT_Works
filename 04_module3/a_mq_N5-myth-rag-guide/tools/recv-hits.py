# -*- coding: utf-8 -*-
"""브라우저가 뽑은 검색 결과를 파일로 받는 수신기 (모듈3 노드5 · 실험 4바퀴)

왜 필요한가. eval-hits 는 **앱의 실제 retrieve()** 로 뽑아야 의미가 있다(검색 로직을
파이썬으로 다시 구현하면 앱과 어긋날 수 있고, 그러면 «앱의 검색»을 잰 게 아니다).
그런데 브라우저는 파일을 직접 못 쓴다. 그래서 잠깐 여는 수신구를 둔다.

쓰는 법
    python tools/recv-hits.py        # Ctrl+C 로 끈다
    (다른 창) 브라우저에서 tools/capture-hits.js 실행

받는 것만 한다 — 경로 이름으로 tools/ 안에 저장한다. 그 밖의 일은 하지 않는다.
"""
import http.server, json, os, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ALLOW = {"eval-hits.json"}          # 덮어써도 되는 파일만 화이트리스트


class H(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_POST(self):
        name = os.path.basename(self.path.strip("/")) or "out.json"
        if name not in ALLOW:
            self.send_response(403); self._cors(); self.end_headers()
            self.wfile.write(b"not allowed")
            print(f"거부 — 허용 목록에 없다: {name}")
            return
        body = self.rfile.read(int(self.headers.get("content-length", 0)))
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception as e:
            self.send_response(400); self._cors(); self.end_headers()
            print(f"거부 — JSON 아님: {e}")
            return
        # 최소 검증 — 13문항이고 hits 가 비지 않았나
        bad = []
        if not isinstance(data, list) or len(data) != 13:
            bad.append(f"문항 수 {len(data) if isinstance(data, list) else '?'} (13이어야 함)")
        else:
            empty = [x.get("id") for x in data if not x.get("hits")]
            if empty:
                bad.append(f"근거가 빈 문항: {empty}")
            myths = {h["id"].split("-")[0] for x in data for h in x.get("hits", [])}
            if myths <= {"greek"}:
                bad.append("후보가 그리스로마뿐 — 6신화를 먼저 불러와야 한다")
        path = os.path.join(HERE, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        self.send_response(200); self._cors(); self.end_headers()
        self.wfile.write(b"ok")
        print(f"저장 — {path} ({len(body)/1024:.0f} KB)")
        for b in bad:
            print(f"  ⚠ {b}")
        if not bad:
            print("  ✅ 검증 통과. python tools/round4-precheck.py 로 다시 확인해라.")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("수신기 대기 — http://127.0.0.1:8899/eval-hits.json (Ctrl+C 로 종료)")
    http.server.HTTPServer(("127.0.0.1", 8899), H).serve_forever()
