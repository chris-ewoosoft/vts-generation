from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import create_tables
from routers.chunks import router as chunks_router
from routers.generate import router as generate_router


app = FastAPI(title="RAG VTS Requirement Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    await create_tables()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


app.include_router(generate_router)
app.include_router(chunks_router)
