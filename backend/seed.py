import asyncio

from sqlalchemy import select

from database import SessionLocal, create_tables
from models import RAGChunk
from services.embedding_service import get_embedding


SEED_CHUNKS = [
    {
        "title": "Background section format",
        "section": "background",
        "content": """Background phải giải thích:
1. Bối cảnh hiện tại của công ty/team (what exists now)
2. Vấn đề đang gặp phải (pain points)
3. Tại sao cần giải quyết ngay (urgency)
Format: 1-2 đoạn văn súc tích, sau đó bullet points liệt kê nhu cầu cụ thể.
Ví dụ: \"The company is expanding its capability in X for Y. Currently, there is no standardized Z.\"
Tiếp theo bullet: Standardize learning content / Reduce onboarding time / Improve consistency""",
    },
    {
        "title": "Purpose section format",
        "section": "purpose",
        "content": """Purpose phải liệt kê 3-5 mục tiêu cụ thể, đo lường được.
Format: \"The purpose of this task is to:\" + numbered list
Mỗi mục phải là action verb + deliverable cụ thể.
Ví dụ:
1. Create standardized [X] documentation
2. Build a practical [Y] roadmap for employees
3. Define evaluation criteria and assessment methods
4. Produce example outputs/images for reference""",
    },
    {
        "title": "Process section format - 3 steps",
        "section": "process",
        "content": """Process thường chia 3 bước:
Step 1 - Create [Documentation/Design/Plan]
Tasks: (bullet points công việc cụ thể)
• Task 1
• Task 2

Step 2 - Execute [Training/Implementation/Review]
Tasks:
• Task 1

Step 3 - Evaluation & Assessment
Tasks:
• Conduct review sessions
• Measure improvement/results

Mỗi task phải actionable và assignable cho 1 developer.""",
    },
    {
        "title": "Considerable factors - when to write NA",
        "section": "considerable_factors",
        "content": """Considerable factors ghi NA nếu task không có dependencies hoặc rủi ro đặc biệt.
Nếu có, ghi: external dependencies, technical constraints, timeline risks, resource requirements.
Ví dụ có nội dung: \"Depends on Ez3D-i bug list being finalized before Step 2. Requires access to staging environment.\"
Ví dụ NA: Task đơn giản, không phụ thuộc hệ thống ngoài -> ghi \"NA\".""",
    },
    {
        "title": "Resulting image / expected outcome",
        "section": "resulting_image",
        "content": """Resulting Image (Expected Outcomes) dùng bullet points mô tả:
• Các deliverables cụ thể được tạo ra
• Kỹ năng/năng lực mà team có được
• Trạng thái của hệ thống sau khi hoàn thành
Ví dụ:
• Training documents are completed and reviewed
• Sample outputs/images are prepared
• Team members can cross functions in [project]
Không viết mục tiêu chung chung, phải cụ thể và verifiable.""",
    },
]


async def seed() -> None:
    await create_tables()

    async with SessionLocal() as db:
        for item in SEED_CHUNKS:
            existing = await db.execute(select(RAGChunk).where(RAGChunk.title == item["title"]))
            chunk = existing.scalar_one_or_none()

            embedding = await get_embedding(f"{item['title']}\n{item['content']}")
            if chunk:
                chunk.content = item["content"]
                chunk.section = item["section"]
                chunk.embedding = embedding
            else:
                db.add(
                    RAGChunk(
                        title=item["title"],
                        content=item["content"],
                        section=item["section"],
                        embedding=embedding,
                        metadata_={},
                    )
                )

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
