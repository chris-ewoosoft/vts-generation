import httpx
import asyncio
import time

async def test_generate():
    prompt = """Based on the following requirement, generate a JSON response with these exact fields:
    - background
    - purpose
    - process
    - considerable_factors
    - resulting_image
    
    Requirement: The application should validate user input before processing."""
    
    schema = {
        "type": "object",
        "properties": {
            "background": {"type": "string"},
            "purpose": {"type": "string"},
            "process": {"type": "string"},
            "considerable_factors": {"type": "string"},
            "resulting_image": {"type": "string"},
        },
        "required": ["background", "purpose", "process", "considerable_factors", "resulting_image"],
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        print(f"Starting LLM generation at {time.time()}")
        try:
            resp = await client.post(
                "http://172.76.10.246:11434/api/generate",
                json={
                    "model": "software-ai:latest",
                    "prompt": prompt,
                    "stream": False,
                    "format": schema,
                    "options": {"temperature": 0.1, "top_p": 0.9}
                }
            )
            print(f"Generation completed at {time.time()}")
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                body = resp.json()
                response_text = body.get("response", "")[:200]
                print(f"Response preview: {response_text}")
            else:
                print(f"Error: {resp.text[:200]}")
        except Exception as e:
            print(f"Exception: {type(e).__name__}: {e}")

asyncio.run(test_generate())
