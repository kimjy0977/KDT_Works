from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
from pathlib import Path

# FastAPI() = 우리 백엔드 서버 본체.
app = FastAPI(title="Opening Trainer API")

# ── 데이터를 저장할 JSON 파일 (서버 꺼도 여기 남음 = 영속성) ──
DATA_FILE = Path("openings.json")

def load_openings():
    # 파일이 있으면 읽어서 리스트로, 없으면 빈 리스트
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return []

def save_openings(openings):
    # 리스트를 JSON으로 파일에 씀
    DATA_FILE.write_text(
        json.dumps(openings, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

# ── 오프닝의 "모양" = 받을 데이터 형식 (FastAPI가 이걸로 자동 검증) ──
class Opening(BaseModel):
    name: str        # 오프닝 이름 (예: 시칠리안 디펜스)
    moves: str       # 수순 (예: 1.e4 c5)
    note: str = ""   # 메모 (선택, 기본값 빈 문자열)


# ── M1: 살아있어? ──
@app.get("/health")
def health():
    return {"status": "ok"}


# ── M3: 웹페이지(프론트) 서빙 — "/" 로 들어오면 index.html 보여줌 ──
@app.get("/")
def home():
    return FileResponse("static/index.html")


# ── 저장: POST /openings ──
@app.post("/openings")
def create_opening(opening: Opening):
    openings = load_openings()        # 기존 것 불러오기
    new = opening.model_dump()        # 받은 데이터를 dict로
    new["id"] = len(openings) + 1     # 간단한 id 부여
    openings.append(new)              # 목록에 추가
    save_openings(openings)           # 파일에 저장
    return new                        # 저장된 것 돌려줌


# ── 목록: GET /openings ──
@app.get("/openings")
def list_openings():
    return load_openings()


# ── 상세: GET /openings/{id} ──
@app.get("/openings/{opening_id}")
def get_opening(opening_id: int):
    openings = load_openings()
    for o in openings:
        if o["id"] == opening_id:
            return o
    raise HTTPException(status_code=404, detail="해당 오프닝 없음")
