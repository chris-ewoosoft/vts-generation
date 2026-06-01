import httpx
import asyncio

async def test_embedding():
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "http://172.76.10.246:11434/api/embeddings",
            json={"model": "bge-m3:latest", "prompt": "test requirement"}
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            body = resp.json()
            if "embedding" in body:
                embedding = body["embedding"]
                print(f"Embedding shape: {len(embedding)} dimensions")
                print(f"First 5 values: {embedding[:5]}")
        else:
            print(f"Error: {resp.text[:200]}")

asyncio.run(test_embedding())
