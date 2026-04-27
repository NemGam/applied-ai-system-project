from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from backend.api.routes import router
from backend.src.ai_pipeline import load_lyrics_index
from backend.src.recommender import load_songs

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

DATA_PATH = ROOT_DIR / "backend" / "data" / "songs.csv"
AUDIO_DIR = ROOT_DIR / "backend" / "audio"
COVERS_DIR = ROOT_DIR / "backend" / "covers"
LYRICS_DIR = ROOT_DIR / "backend" / "lyrics"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.songs = load_songs(str(DATA_PATH))
    app.state.lyrics_by_song_id = load_lyrics_index(LYRICS_DIR)
    yield


app = FastAPI(
    title="Music Recommender API",
    version="0.1.0",
    description="Minimal FastAPI wrapper around the local song recommender.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")
app.mount("/covers", StaticFiles(directory=COVERS_DIR), name="covers")
app.include_router(router)
