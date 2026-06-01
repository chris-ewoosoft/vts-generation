# Copilot Prompt: RAG-powered VTS Requirement Generator

## Tá»•ng quan dá»± Ã¡n

XÃ¢y dá»±ng má»™t full-stack web application cho phÃ©p:
1. NgÆ°á»i dÃ¹ng nháº­p yÃªu cáº§u tá»± nhiÃªn â†’ AI tá»± Ä‘á»™ng format thÃ nh VTS ticket chuáº©n 5-section
2. Quáº£n lÃ½ RAG knowledge base (chunks): xem, thÃªm, sá»­a, xÃ³a Ä‘á»ƒ cáº­p nháº­t rule

**Stack báº¯t buá»™c** (tá»« .env cÃ³ sáºµn):
- Database: **PostgreSQL** (vá»›i extension **pgvector** cho vector search)
- LLM & Embedding: **Ollama** (cháº¡y local)
- Backend: **Python + FastAPI**
- Frontend: **React + Vite + TailwindCSS**

---

## Cáº¥u trÃºc thÆ° má»¥c

```
project/
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ main.py
â”‚   â”œâ”€â”€ config.py
â”‚   â”œâ”€â”€ database.py
â”‚   â”œâ”€â”€ models.py
â”‚   â”œâ”€â”€ routers/
â”‚   â”‚   â”œâ”€â”€ generate.py
â”‚   â”‚   â””â”€â”€ chunks.py
â”‚   â”œâ”€â”€ services/
â”‚   â”‚   â”œâ”€â”€ rag_service.py
â”‚   â”‚   â”œâ”€â”€ embedding_service.py
â”‚   â”‚   â””â”€â”€ llm_service.py
â”‚   â”œâ”€â”€ requirements.txt
â”‚   â””â”€â”€ .env
â”œâ”€â”€ frontend/
â”‚   â”œâ”€â”€ src/
â”‚   â”‚   â”œâ”€â”€ pages/
â”‚   â”‚   â”‚   â”œâ”€â”€ GeneratePage.tsx
â”‚   â”‚   â”‚   â””â”€â”€ ChunkManagerPage.tsx
â”‚   â”‚   â”œâ”€â”€ components/
â”‚   â”‚   â”‚   â”œâ”€â”€ RequirementForm.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ VTSOutput.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ ChunkList.tsx
â”‚   â”‚   â”‚   â””â”€â”€ ChunkEditor.tsx
â”‚   â”‚   â”œâ”€â”€ api/
â”‚   â”‚   â”‚   â””â”€â”€ client.ts
â”‚   â”‚   â””â”€â”€ App.tsx
â”‚   â””â”€â”€ package.json
â””â”€â”€ docker-compose.yml
```

---

## BÆ°á»›c 1: Cáº¥u hÃ¬nh `.env` (backend)

```env
# PostgreSQL (cÃ³ sáºµn)
DATABASE_URL=postgresql://user:password@localhost:5432/vts_rag_db

# Ollama (cÃ³ sáºµn, cháº¡y local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_LLM_MODEL=llama3.2

# App config
CHUNK_TOP_K=5
```

---

## BÆ°á»›c 2: Database Schema (PostgreSQL + pgvector)

Táº¡o file `backend/database.py` vÃ  cháº¡y migration:

```sql
-- KÃ­ch hoáº¡t pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Báº£ng lÆ°u RAG chunks (rules/context cho LLM)
CREATE TABLE rag_chunks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       VARCHAR(255) NOT NULL,
    content     TEXT NOT NULL,
    section     VARCHAR(50),  -- 'background' | 'purpose' | 'process' | 'considerable_factors' | 'resulting_image' | 'general'
    embedding   vector(768),  -- nomic-embed-text = 768 dims; Ä‘á»•i náº¿u dÃ¹ng model khÃ¡c
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- Index cho similarity search
CREATE INDEX ON rag_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Báº£ng lÆ°u lá»‹ch sá»­ generate (optional, tá»‘t Ä‘á»ƒ audit)
CREATE TABLE generation_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_input      TEXT NOT NULL,
    output_json     JSONB NOT NULL,  -- {background, purpose, process, considerable_factors, resulting_image}
    chunks_used     UUID[],
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

## BÆ°á»›c 3: SQLAlchemy Models (`backend/models.py`)

```python
from sqlalchemy import Column, String, Text, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class RAGChunk(Base):
    __tablename__ = "rag_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    section = Column(String(50), nullable=True)
    embedding = Column(Vector(768), nullable=True)
    metadata_ = Column("metadata", JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GenerationHistory(Base):
    __tablename__ = "generation_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_input = Column(Text, nullable=False)
    output_json = Column(JSONB, nullable=False)
    chunks_used = Column(ARRAY(UUID(as_uuid=True)), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## BÆ°á»›c 4: Embedding Service (`backend/services/embedding_service.py`)

```python
import httpx
from config import settings

async def get_embedding(text: str) -> list[float]:
    """Gá»i Ollama Ä‘á»ƒ láº¥y embedding vector cá»§a text."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/embeddings",
            json={
                "model": settings.OLLAMA_EMBED_MODEL,
                "prompt": text
            }
        )
        response.raise_for_status()
        return response.json()["embedding"]
```

---

## BÆ°á»›c 5: RAG Service (`backend/services/rag_service.py`)

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from services.embedding_service import get_embedding
from config import settings

async def retrieve_relevant_chunks(query: str, db: AsyncSession, section_filter: str = None) -> list[dict]:
    """
    1. Embed query báº±ng Ollama
    2. TÃ¬m top-K chunks gáº§n nháº¥t báº±ng cosine similarity (pgvector)
    3. Optional: filter theo section
    """
    query_embedding = await get_embedding(query)
    embedding_str = f"[{','.join(map(str, query_embedding))}]"
    
    filter_clause = ""
    if section_filter:
        filter_clause = f"AND (section = '{section_filter}' OR section = 'general')"
    
    sql = text(f"""
        SELECT id, title, content, section,
               1 - (embedding <=> '{embedding_str}'::vector) AS similarity
        FROM rag_chunks
        WHERE embedding IS NOT NULL {filter_clause}
        ORDER BY embedding <=> '{embedding_str}'::vector
        LIMIT :top_k
    """)
    
    result = await db.execute(sql, {"top_k": settings.CHUNK_TOP_K})
    rows = result.fetchall()
    
    return [
        {"id": str(r.id), "title": r.title, "content": r.content, 
         "section": r.section, "similarity": float(r.similarity)}
        for r in rows
    ]

def build_rag_prompt(user_input: str, chunks: list[dict]) -> str:
    """Build prompt vá»›i context tá»« RAG chunks."""
    context = "\n\n".join([
        f"[Rule/Example - {c['section'] or 'general'}]\n{c['content']}"
        for c in chunks
    ])
    
    return f"""Báº¡n lÃ  má»™t senior developer chuyÃªn viáº¿t VTS requirement tickets.
DÆ°á»›i Ä‘Ã¢y lÃ  cÃ¡c rules vÃ  examples tá»« knowledge base:

{context}

---
Dá»±a vÃ o rules/examples trÃªn, hÃ£y viáº¿t VTS requirement ticket cho yÃªu cáº§u sau:

"{user_input}"

Báº¯t buá»™c output ra JSON vá»›i Ä‘Ãºng format sau (khÃ´ng thÃªm text ngoÃ i JSON):
{{
  "background": "MÃ´ táº£ bá»‘i cáº£nh, lÃ½ do cáº§n lÃ m feature nÃ y. NÃªu váº¥n Ä‘á» hiá»‡n táº¡i vÃ  táº¡i sao cáº§n giáº£i quyáº¿t.",
  "purpose": "Má»¥c Ä‘Ã­ch cá»¥ thá»ƒ cá»§a task. Liá»‡t kÃª 3-5 má»¥c tiÃªu dÆ°á»›i dáº¡ng numbered list.",
  "process": "CÃ¡c bÆ°á»›c thá»±c hiá»‡n chi tiáº¿t. Chia thÃ nh cÃ¡c Step vá»›i Tasks cá»¥ thá»ƒ. Format: Step 1 â€” TÃªn bÆ°á»›c\\nTasks\\nâ€¢ task 1\\nâ€¢ task 2",
  "considerable_factors": "CÃ¡c yáº¿u tá»‘ cáº§n xem xÃ©t, rá»§i ro, dependencies. Náº¿u khÃ´ng cÃ³ ghi NA.",
  "resulting_image": "Káº¿t quáº£ mong Ä‘á»£i sau khi hoÃ n thÃ nh. Liá»‡t kÃª dáº¡ng bullet points."
}}"""
```

---

## BÆ°á»›c 6: LLM Service (`backend/services/llm_service.py`)

```python
import httpx
import json
from config import settings

async def generate_with_ollama(prompt: str) -> dict:
    """Gá»i Ollama Ä‘á»ƒ generate VTS requirement JSON."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": settings.OLLAMA_LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",  # Ollama JSON mode
                "options": {
                    "temperature": 0.3,  # tháº¥p Ä‘á»ƒ output nháº¥t quÃ¡n
                    "top_p": 0.9,
                }
            }
        )
        response.raise_for_status()
        raw = response.json()["response"]
        
        # Parse JSON tá»« response
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Fallback: extract JSON tá»« text náº¿u cÃ³ extra content
            import re
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError(f"KhÃ´ng parse Ä‘Æ°á»£c JSON tá»« LLM response: {raw[:200]}")
```

---

## BÆ°á»›c 7: API Routers

### `backend/routers/generate.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services.rag_service import retrieve_relevant_chunks, build_rag_prompt
from services.llm_service import generate_with_ollama
from models import GenerationHistory
from pydantic import BaseModel

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
async def generate_requirement(req: GenerateRequest, db: AsyncSession = Depends(get_db)):
    # 1. Retrieve relevant chunks
    chunks = await retrieve_relevant_chunks(req.user_input, db)
    
    # 2. Build prompt vá»›i RAG context
    prompt = build_rag_prompt(req.user_input, chunks)
    
    # 3. Generate vá»›i Ollama
    output = await generate_with_ollama(prompt)
    
    # 4. LÆ°u lá»‹ch sá»­ (optional)
    history = GenerationHistory(
        user_input=req.user_input,
        output_json=output,
        chunks_used=[c["id"] for c in chunks]
    )
    db.add(history)
    await db.commit()
    
    return output
```

### `backend/routers/chunks.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database import get_db
from models import RAGChunk
from services.embedding_service import get_embedding
from pydantic import BaseModel
from typing import Optional
import uuid

router = APIRouter(prefix="/api/chunks", tags=["chunks"])

class ChunkCreate(BaseModel):
    title: str
    content: str
    section: Optional[str] = "general"  # background|purpose|process|considerable_factors|resulting_image|general
    metadata: Optional[dict] = {}

class ChunkUpdate(BaseModel):
    title: Optional[str]
    content: Optional[str]
    section: Optional[str]
    metadata: Optional[dict]

@router.get("/")
async def list_chunks(section: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(RAGChunk).order_by(RAGChunk.created_at.desc())
    if section:
        query = query.where(RAGChunk.section == section)
    result = await db.execute(query)
    chunks = result.scalars().all()
    return [
        {"id": str(c.id), "title": c.title, "content": c.content, 
         "section": c.section, "metadata": c.metadata_, 
         "created_at": c.created_at, "updated_at": c.updated_at}
        for c in chunks
    ]

@router.post("/", status_code=201)
async def create_chunk(data: ChunkCreate, db: AsyncSession = Depends(get_db)):
    # Táº¡o embedding ngay khi thÃªm chunk
    embedding = await get_embedding(f"{data.title}\n{data.content}")
    
    chunk = RAGChunk(
        title=data.title,
        content=data.content,
        section=data.section,
        embedding=embedding,
        metadata_=data.metadata
    )
    db.add(chunk)
    await db.commit()
    await db.refresh(chunk)
    return {"id": str(chunk.id), "message": "Chunk created successfully"}

@router.put("/{chunk_id}")
async def update_chunk(chunk_id: str, data: ChunkUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RAGChunk).where(RAGChunk.id == uuid.UUID(chunk_id)))
    chunk = result.scalar_one_or_none()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")
    
    if data.title is not None: chunk.title = data.title
    if data.content is not None: chunk.content = data.content
    if data.section is not None: chunk.section = data.section
    if data.metadata is not None: chunk.metadata_ = data.metadata
    
    # Re-embed náº¿u content thay Ä‘á»•i
    if data.content or data.title:
        chunk.embedding = await get_embedding(f"{chunk.title}\n{chunk.content}")
    
    await db.commit()
    return {"message": "Chunk updated successfully"}

@router.delete("/{chunk_id}")
async def delete_chunk(chunk_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        delete(RAGChunk).where(RAGChunk.id == uuid.UUID(chunk_id))
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Chunk not found")
    await db.commit()
    return {"message": "Chunk deleted successfully"}
```

---

## BÆ°á»›c 8: Frontend React

### `frontend/src/pages/GeneratePage.tsx`

```tsx
import { useState } from 'react'
import { generateRequirement } from '../api/client'
import VTSOutput from '../components/VTSOutput'

export default function GeneratePage() {
  const [input, setInput] = useState('')
  const [output, setOutput] = useState<null | Record<string, string>>(null)
  const [loading, setLoading] = useState(false)

  const handleGenerate = async () => {
    if (!input.trim()) return
    setLoading(true)
    try {
      const result = await generateRequirement(input)
      setOutput(result)
    } catch (e) {
      alert('Lá»—i khi generate. Kiá»ƒm tra Ollama Ä‘ang cháº¡y.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-semibold mb-6 text-gray-800">
        VTS Requirement Generator
      </h1>
      
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          MÃ´ táº£ yÃªu cáº§u cá»§a báº¡n
        </label>
        <textarea
          className="w-full border border-gray-300 rounded-lg p-3 h-36 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="VD: Cáº§n xÃ¢y dá»±ng há»‡ thá»‘ng training 3D ná»™i bá»™ cho team..."
          value={input}
          onChange={e => setInput(e.target.value)}
        />
      </div>
      
      <button
        onClick={handleGenerate}
        disabled={loading || !input.trim()}
        className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition"
      >
        {loading ? 'Äang xá»­ lÃ½...' : 'Generate Requirement'}
      </button>

      {output && <VTSOutput data={output} />}
    </div>
  )
}
```

### `frontend/src/components/VTSOutput.tsx`

```tsx
// Hiá»ƒn thá»‹ output theo 5-section VTS format (nhÆ° áº£nh máº«u)
const SECTIONS = [
  { key: 'background',            label: 'Background' },
  { key: 'purpose',               label: 'Purpose' },
  { key: 'process',               label: 'Process\n(including request items)' },
  { key: 'considerable_factors',  label: 'Considerable factors' },
  { key: 'resulting_image',       label: 'Resulting Image' },
]

export default function VTSOutput({ data }: { data: Record<string, string> }) {
  const copyAll = () => {
    const text = SECTIONS.map(s => `### ${s.label}\n${data[s.key]}`).join('\n\n')
    navigator.clipboard.writeText(text)
  }

  return (
    <div className="mt-8 border border-gray-200 rounded-xl overflow-hidden shadow-sm">
      <div className="flex justify-between items-center bg-gray-50 px-4 py-3 border-b border-gray-200">
        <span className="font-semibold text-gray-700">VTS Requirement</span>
        <button onClick={copyAll} className="text-sm text-indigo-600 hover:underline">
          Copy all
        </button>
      </div>
      
      {SECTIONS.map(({ key, label }) => (
        <div key={key} className="flex border-b border-gray-100 last:border-b-0">
          {/* Label column - dark sidebar nhÆ° áº£nh máº«u */}
          <div className="w-36 shrink-0 bg-gray-700 text-gray-200 text-xs font-medium p-4 flex items-start">
            <span className="whitespace-pre-line">{label}</span>
          </div>
          {/* Content column */}
          <div className="flex-1 p-4 text-sm text-gray-700 whitespace-pre-wrap bg-white">
            {data[key] || 'â€”'}
          </div>
        </div>
      ))}
    </div>
  )
}
```

### `frontend/src/pages/ChunkManagerPage.tsx`

```tsx
// Trang quáº£n lÃ½ RAG chunks: list, add, edit, delete
import { useEffect, useState } from 'react'
import { getChunks, createChunk, updateChunk, deleteChunk } from '../api/client'
import ChunkList from '../components/ChunkList'
import ChunkEditor from '../components/ChunkEditor'

const SECTIONS = ['general','background','purpose','process','considerable_factors','resulting_image']

export default function ChunkManagerPage() {
  const [chunks, setChunks] = useState([])
  const [filter, setFilter] = useState('')
  const [editing, setEditing] = useState<any>(null)   // null = add new
  const [showEditor, setShowEditor] = useState(false)

  const load = async () => setChunks(await getChunks(filter))
  useEffect(() => { load() }, [filter])

  const handleSave = async (data: any) => {
    if (data.id) await updateChunk(data.id, data)
    else await createChunk(data)
    setShowEditor(false)
    load()
  }

  const handleDelete = async (id: string) => {
    if (!confirm('XÃ³a chunk nÃ y?')) return
    await deleteChunk(id)
    load()
  }

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-800">RAG Chunk Manager</h1>
        <button
          onClick={() => { setEditing(null); setShowEditor(true) }}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
        >
          + Add Chunk
        </button>
      </div>

      {/* Filter by section */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {['', ...SECTIONS].map(s => (
          <button key={s} onClick={() => setFilter(s)}
            className={`px-3 py-1 rounded-full text-sm border transition
              ${filter === s ? 'bg-indigo-600 text-white border-indigo-600' : 'border-gray-300 text-gray-600 hover:border-indigo-400'}`}>
            {s || 'All'}
          </button>
        ))}
      </div>

      <ChunkList chunks={chunks} onEdit={c => { setEditing(c); setShowEditor(true) }} onDelete={handleDelete} />
      
      {showEditor && (
        <ChunkEditor
          chunk={editing}
          sections={SECTIONS}
          onSave={handleSave}
          onClose={() => setShowEditor(false)}
        />
      )}
    </div>
  )
}
```

---

## BÆ°á»›c 9: API Client (`frontend/src/api/client.ts`)

```typescript
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const generateRequirement = async (user_input: string) => {
  const res = await fetch(`${BASE}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_input })
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const getChunks = async (section?: string) => {
  const params = section ? `?section=${section}` : ''
  const res = await fetch(`${BASE}/api/chunks${params}`)
  return res.json()
}

export const createChunk = async (data: any) => {
  const res = await fetch(`${BASE}/api/chunks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  return res.json()
}

export const updateChunk = async (id: string, data: any) => {
  const res = await fetch(`${BASE}/api/chunks/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  return res.json()
}

export const deleteChunk = async (id: string) => {
  await fetch(`${BASE}/api/chunks/${id}`, { method: 'DELETE' })
}
```

---

## BÆ°á»›c 10: Seed Data - RAG Chunks máº«u

ThÃªm cÃ¡c chunks sau vÃ o database lÃ m knowledge base khá»Ÿi Ä‘áº§u:

```python
SEED_CHUNKS = [
  {
    "title": "Background section format",
    "section": "background",
    "content": """Background pháº£i giáº£i thÃ­ch:
1. Bá»‘i cáº£nh hiá»‡n táº¡i cá»§a cÃ´ng ty/team (what exists now)
2. Váº¥n Ä‘á» Ä‘ang gáº·p pháº£i (pain points)
3. Táº¡i sao cáº§n giáº£i quyáº¿t ngay (urgency)
Format: 1-2 Ä‘oáº¡n vÄƒn sÃºc tÃ­ch, sau Ä‘Ã³ bullet points liá»‡t kÃª nhu cáº§u cá»¥ thá»ƒ.
VÃ­ dá»¥: "The company is expanding its capability in X for Y. Currently, there is no standardized Z."
Tiáº¿p theo bullet: Standardize learning content / Reduce onboarding time / Improve consistency"""
  },
  {
    "title": "Purpose section format",
    "section": "purpose",
    "content": """Purpose pháº£i liá»‡t kÃª 3-5 má»¥c tiÃªu cá»¥ thá»ƒ, Ä‘o lÆ°á»ng Ä‘Æ°á»£c.
Format: "The purpose of this task is to:" + numbered list
Má»—i má»¥c pháº£i lÃ  action verb + deliverable cá»¥ thá»ƒ.
VÃ­ dá»¥:
1. Create standardized [X] documentation
2. Build a practical [Y] roadmap for employees
3. Define evaluation criteria and assessment methods
4. Produce example outputs/images for reference"""
  },
  {
    "title": "Process section format - 3 steps",
    "section": "process",
    "content": """Process thÆ°á»ng chia 3 bÆ°á»›c:
Step 1 â€” Create [Documentation/Design/Plan]
Tasks: (bullet points cÃ´ng viá»‡c cá»¥ thá»ƒ)
â€¢ Task 1
â€¢ Task 2

Step 2 â€” Execute [Training/Implementation/Review]
Tasks:
â€¢ Task 1

Step 3 â€” Evaluation & Assessment
Tasks:
â€¢ Conduct review sessions
â€¢ Measure improvement/results

Má»—i task pháº£i actionable vÃ  assignable cho 1 developer."""
  },
  {
    "title": "Considerable factors - when to write NA",
    "section": "considerable_factors",
    "content": """Considerable factors ghi NA náº¿u task khÃ´ng cÃ³ dependencies hoáº·c rá»§i ro Ä‘áº·c biá»‡t.
Náº¿u cÃ³, ghi: external dependencies, technical constraints, timeline risks, resource requirements.
VÃ­ dá»¥ cÃ³ ná»™i dung: "Depends on Ez3D-i bug list being finalized before Step 2. Requires access to staging environment."
VÃ­ dá»¥ NA: Task Ä‘Æ¡n giáº£n, khÃ´ng phá»¥ thuá»™c há»‡ thá»‘ng ngoÃ i â†’ ghi "NA"."""
  },
  {
    "title": "Resulting image / expected outcome",
    "section": "resulting_image",
    "content": """Resulting Image (Expected Outcomes) dÃ¹ng bullet points mÃ´ táº£:
â€¢ CÃ¡c deliverables cá»¥ thá»ƒ Ä‘Æ°á»£c táº¡o ra
â€¢ Ká»¹ nÄƒng/nÄƒng lá»±c mÃ  team cÃ³ Ä‘Æ°á»£c
â€¢ Tráº¡ng thÃ¡i cá»§a há»‡ thá»‘ng sau khi hoÃ n thÃ nh
VÃ­ dá»¥:
â€¢ Training documents are completed and reviewed
â€¢ Sample outputs/images are prepared
â€¢ Team members can cross functions in [project]
KhÃ´ng viáº¿t má»¥c tiÃªu chung chung, pháº£i cá»¥ thá»ƒ vÃ  verifiable."""
  },
]
```

---

## BÆ°á»›c 11: `requirements.txt`

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.35
asyncpg==0.29.0
pgvector==0.3.3
httpx==0.27.0
python-dotenv==1.0.1
pydantic==2.9.0
alembic==1.13.0
```

---

## BÆ°á»›c 12: Khá»Ÿi cháº¡y

```bash
# 1. CÃ i pgvector extension (náº¿u chÆ°a cÃ³)
psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 2. Cháº¡y migration
cd backend && python -c "from database import create_tables; import asyncio; asyncio.run(create_tables())"

# 3. Seed initial chunks
cd backend && python seed.py

# 4. Start backend
uvicorn main:app --reload --port 8000

# 5. Start frontend
cd frontend && npm install && npm run dev
```

---

## Äiá»ƒm quan trá»ng cáº§n lÆ°u Ã½ cho Copilot

1. **Ollama pháº£i Ä‘ang cháº¡y** vá»›i 2 model: `nomic-embed-text` (embedding) vÃ  `llama3.2` (generation)
2. **pgvector dimension** pháº£i khá»›p vá»›i model: `nomic-embed-text` = 768 dims
3. **JSON format mode** cá»§a Ollama: dÃ¹ng `"format": "json"` Ä‘á»ƒ LLM tráº£ vá» JSON clean
4. **Re-embedding**: khi update chunk content, pháº£i re-embed Ä‘á»ƒ vector search váº«n chÃ­nh xÃ¡c
5. **Section filter**: retrieve chunks theo section giÃºp context táº­p trung hÆ¡n (background section chá»‰ láº¥y background chunks)
6. **Temperature tháº¥p (0.3)**: Ä‘á»ƒ output consistent, khÃ´ng quÃ¡ creative
7. **CORS**: FastAPI cáº§n `CORSMiddleware` cho frontend dev server (localhost:5173)



