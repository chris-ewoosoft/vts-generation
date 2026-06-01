import httpx

from config import settings


async def get_embedding(text: str) -> list[float]:
    """Call Ollama embedding endpoint and return embedding vector."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Try legacy endpoint first (/api/embeddings), then modern endpoint (/api/embed).
        candidates = [
            (
                f"{settings.ollama_base_url}/api/embeddings",
                {
                    "model": settings.ollama_embed_model,
                    "prompt": text,
                },
            ),
            (
                f"{settings.ollama_base_url}/api/embed",
                {
                    "model": settings.ollama_embed_model,
                    "input": text,
                },
            ),
        ]

        last_error: Exception | None = None
        for url, payload in candidates:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                body = response.json()

                # /api/embeddings shape
                if isinstance(body.get("embedding"), list):
                    return body["embedding"]

                # /api/embed shape
                embeddings = body.get("embeddings")
                if isinstance(embeddings, list) and embeddings and isinstance(embeddings[0], list):
                    return embeddings[0]

                raise ValueError("Embedding response format is invalid")
            except Exception as exc:  # pragma: no cover - network/service variance
                last_error = exc

        raise ValueError(f"Cannot get embedding from Ollama: {last_error}")
