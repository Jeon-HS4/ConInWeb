from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import asyncpg

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# PostgreSQL 데이터베이스 연결 설정
DB_HOST = '127.0.0.1'
DB_PORT = '5432'
DB_USER = 'aiddb'
DB_PASSWORD = 'aid'
DB_NAME = 'conference'

# 학회 정보 캐시
conferences_cache = []

async def load_conferences():
    """학회 정보를 PostgreSQL에서 로드하고 캐싱합니다."""
    global conferences_cache
    conn = await asyncpg.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASSWORD,
        database=DB_NAME
    )
    query = """
    SELECT name, description, conference_start_date, conference_end_date, location, image_path
    FROM conferences
    """
    conferences_cache = await conn.fetch(query)
    conferences_cache = [
        {
            "name": conference['name'],
            "description": conference['description'],
            "conference_start_date": str(conference['conference_start_date']) if conference['conference_start_date'] else None,
            "conference_end_date": str(conference['conference_end_date']) if conference['conference_end_date'] else None,
            "location": conference['location'],
            "image_path": conference['image_path']
        }
        for conference in conferences_cache
    ]
    await conn.close()
    
@app.on_event("startup")
async def startup_event():
    """서버 시작 시 학회 정보를 캐싱합니다."""
    await load_conferences()

@app.get("/")
async def get_calendar(request: Request):
    """캐싱된 학회 정보를 사용하여 캘린더 페이지를 렌더링합니다."""
    return templates.TemplateResponse("new_cal.html", {"request": request, "conferences": conferences_cache})

@app.get("/event/{date}")
async def get_event_detail(request: Request, date: str):
    """특정 날짜에 해당하는 학회 정보를 반환합니다."""
    event = next((conf for conf in conferences_cache if conf["conference_start_date"] == date), None)
    if event:
        return templates.TemplateResponse("event_detail.html", {"request": request, "event": event})
    else:
        return {"error": "Event not found"}
