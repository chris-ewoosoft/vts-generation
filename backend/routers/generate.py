from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import GenerationHistory
from services.llm_service import generate_with_ollama
from services.rag_service import build_rag_prompt, retrieve_relevant_chunks


router = APIRouter(prefix="/api", tags=["generate"])


class GenerateRequest(BaseModel):
    user_input: str


class VTSOutput(BaseModel):
    background: str
    purpose: str
    process: str
    considerable_factors: str
    resulting_image: str


@router.post("/generate", response_model=VTSOutput)
async def generate_requirement(
    req: GenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> VTSOutput:
    chunks = await retrieve_relevant_chunks(req.user_input, db)
    prompt = build_rag_prompt(req.user_input, chunks)
    try:
        # generate_with_ollama already returns a sanitized dict with only str values.
        output = await generate_with_ollama(prompt)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM generate failed: {exc}") from exc

    history = GenerationHistory(
        user_input=req.user_input,
        output_json=output,
        chunks_used=[chunk["id"] for chunk in chunks],
    )
    db.add(history)
    await db.commit()

    return VTSOutput.model_validate(output)
