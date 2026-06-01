from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from services.embedding_service import get_embedding


async def retrieve_relevant_chunks(
    query: str,
    db: AsyncSession,
    section_filter: str | None = None,
) -> list[dict]:
    """Retrieve top-k chunks by vector similarity, optionally filtered by section."""
    try:
        query_embedding = await get_embedding(query)
    except Exception:
        # Fail-open: still allow generation without RAG context when embedding service is unstable.
        return []

    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

    filter_clause = ""
    params: dict[str, object] = {
        "embedding": embedding_str,
        "top_k": settings.chunk_top_k,
    }
    if section_filter:
        filter_clause = "AND (section = :section_filter OR section = 'general')"
        params["section_filter"] = section_filter

    sql = text(
        f"""
        SELECT id, title, content, section,
               1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
        FROM rag_chunks
        WHERE embedding IS NOT NULL {filter_clause}
        ORDER BY embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
        """
    )

    try:
        result = await db.execute(sql, params)
        rows = result.fetchall()
    except Exception:
        # Fail-open if vector query fails (e.g., dimension mismatch or extension instability).
        return []

    return [
        {
            "id": str(row.id),
            "title": row.title,
            "content": row.content,
            "section": row.section,
            "similarity": float(row.similarity),
        }
        for row in rows
    ]


def build_rag_prompt(user_input: str, chunks: list[dict]) -> str:
    """Build prompt from retrieved chunks and user input."""
    context = "\n\n".join(
        [
            f"[Rule/Example - {chunk.get('section') or 'general'}]\n{chunk['content']}"
            for chunk in chunks
        ]
    )

    return f"""Bạn là một senior developer chuyên viết VTS requirement tickets.
Dưới đây là các rules và examples từ knowledge base:

{context}

Dựa vào rules/examples trên, hãy viết VTS requirement ticket cho yêu cầu sau:

\"{user_input}\"

    Nếu input là bug report (có Reproduction steps / Expected result / Actual result), bắt buộc map như sau:
    - background: nêu bối cảnh lỗi + chênh lệch giữa expected và actual.
    - purpose: mục tiêu sửa lỗi dưới dạng 3-5 mục numbered list.
    - process: chuyển reproduction steps thành các Step/Tasks cụ thể có thể implement và test.
    - considerable_factors: rủi ro, dependencies, edge cases, dữ liệu test cần chuẩn bị.
    - resulting_image: trạng thái mong đợi sau fix, viết rõ tiêu chí pass.

    Chỉ dùng đúng 5 key chuẩn, không đổi tên key, không dùng biến thể key.

Bắt buộc output ra JSON với đúng format sau (không thêm text ngoài JSON):
{{
  \"background\": \"Mô tả bối cảnh, lý do cần làm feature này. Nêu vấn đề hiện tại và tại sao cần giải quyết.\",
  \"purpose\": \"Mục đích cụ thể của task. Liệt kê 3-5 mục tiêu dưới dạng numbered list.\",
  \"process\": \"Các bước thực hiện chi tiết. Chia thành các Step với Tasks cụ thể. Format: Step 1 — Tên bước\\nTasks\\n• task 1\\n• task 2\",
  \"considerable_factors\": \"Các yếu tố cần xem xét, rủi ro, dependencies. Nếu không có ghi NA.\",
  \"resulting_image\": \"Kết quả mong đợi sau khi hoàn thành. Liệt kê dạng bullet points.\"
}}"""
