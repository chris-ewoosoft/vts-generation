import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import RAGChunk
from services.embedding_service import get_embedding


router = APIRouter(prefix="/api/chunks", tags=["chunks"])


class ChunkCreate(BaseModel):
    title: str
    content: str
    section: Optional[str] = "general"
    metadata: dict = Field(default_factory=dict)


class ChunkUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    section: Optional[str] = None
    metadata: Optional[dict] = None


@router.get("/")
async def list_chunks(
    section: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    query = select(RAGChunk).order_by(RAGChunk.created_at.desc())
    if section:
        query = query.where(RAGChunk.section == section)

    result = await db.execute(query)
    chunks = result.scalars().all()

    return [
        {
            "id": str(chunk.id),
            "title": chunk.title,
            "content": chunk.content,
            "section": chunk.section,
            "metadata": chunk.metadata_,
            "created_at": chunk.created_at,
            "updated_at": chunk.updated_at,
        }
        for chunk in chunks
    ]


@router.post("/", status_code=201)
async def create_chunk(data: ChunkCreate, db: AsyncSession = Depends(get_db)) -> dict:
    embedding = None
    warning: str | None = None
    try:
        embedding = await get_embedding(f"{data.title}\n{data.content}")
    except Exception as exc:
        # Allow chunk creation even if embedding service is temporarily unavailable.
        warning = f"Chunk created without embedding: {exc}"

    chunk = RAGChunk(
        title=data.title,
        content=data.content,
        section=data.section,
        embedding=embedding,
        metadata_=data.metadata,
    )

    db.add(chunk)
    await db.commit()
    await db.refresh(chunk)

    response = {"id": str(chunk.id), "message": "Chunk created successfully"}
    if warning:
        response["warning"] = warning
    return response


@router.put("/{chunk_id}")
async def update_chunk(
    chunk_id: str,
    data: ChunkUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        target_id = uuid.UUID(chunk_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid chunk id") from exc

    result = await db.execute(select(RAGChunk).where(RAGChunk.id == target_id))
    chunk = result.scalar_one_or_none()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")

    if data.title is not None:
        chunk.title = data.title
    if data.content is not None:
        chunk.content = data.content
    if data.section is not None:
        chunk.section = data.section
    if data.metadata is not None:
        chunk.metadata_ = data.metadata

    warning: str | None = None
    if data.content is not None or data.title is not None:
        try:
            chunk.embedding = await get_embedding(f"{chunk.title}\n{chunk.content}")
        except Exception as exc:
            chunk.embedding = None
            warning = f"Chunk updated but embedding refresh failed: {exc}"

    await db.commit()

    response = {"message": "Chunk updated successfully"}
    if warning:
        response["warning"] = warning
    return response


@router.delete("/{chunk_id}")
async def delete_chunk(chunk_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        target_id = uuid.UUID(chunk_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid chunk id") from exc

    result = await db.execute(delete(RAGChunk).where(RAGChunk.id == target_id))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Chunk not found")

    await db.commit()
    return {"message": "Chunk deleted successfully"}
