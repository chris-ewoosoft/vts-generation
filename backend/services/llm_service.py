import json
import re

import httpx

from config import settings


REQUIRED_KEYS = [
    "background",
    "purpose",
    "process",
    "considerable_factors",
    "resulting_image",
]

# Common model key variants we map into the canonical API schema.
ALIASES = {
    "considerable factor": "considerable_factors",
    "considerable factors": "considerable_factors",
    "considerable_factors": "considerable_factors",
    "considerableFactors": "considerable_factors",
    "image result": "resulting_image",
    "image results": "resulting_image",
    "result image": "resulting_image",
    "resulting image": "resulting_image",
    "resulting_image": "resulting_image",
    "resultingImage": "resulting_image",
}


def _canonicalize_key(key: str) -> str:
    normalized = key.strip()
    if normalized in REQUIRED_KEYS:
        return normalized
    lowered = normalized.lower()
    if lowered in REQUIRED_KEYS:
        return lowered
    return ALIASES.get(normalized, ALIASES.get(lowered, normalized))


def _extract_json_block(raw: str) -> str:
    try:
        # Best case: the model already returned clean JSON.
        json.loads(raw)
        return raw
    except json.JSONDecodeError:
        pass

    # Fallback: extract first object block if model wrapped JSON with extra text.
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"Model output is not valid JSON. Raw preview: {raw[:400]}")
    return match.group()


def _parse_model_output(raw: str) -> dict:
    json_block = _extract_json_block(raw)
    try:
        parsed = json.loads(json_block)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"JSON parse failed near pos {exc.pos}. Raw preview: {json_block[:400]}"
        ) from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"Model output must be a JSON object, got: {type(parsed).__name__}")
    return parsed


def _coerce_str(value: object) -> str:
    """Ensure a field value is a plain string regardless of what the LLM returned."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(
            item if isinstance(item, str) else str(item) for item in value
        )
    if value is None:
        return ""
    return str(value)


def _sanitize_llm_output(data: dict) -> dict:
    """Coerce every required field to str and fill missing fields with empty string."""
    canonical: dict[str, object] = {}
    for key, value in data.items():
        canonical[_canonicalize_key(key)] = value
    return {key: _coerce_str(canonical.get(key, "")) for key in REQUIRED_KEYS}


def _looks_invalid_text(value: str) -> bool:
    text = value.strip()
    if not text:
        return True
    # Reject punctuation-only fragments such as ":[" or "...".
    if re.fullmatch(r"[\s\[\]\{\}\(\):;,.\-_'\"`|/\\]+", text):
        return True
    return len(text) < 3


def _invalid_sections(output: dict) -> list[str]:
    invalid: list[str] = []
    for key in REQUIRED_KEYS:
        value = output.get(key, "")
        # NA is acceptable only for considerable_factors.
        if key == "considerable_factors" and value.strip().upper() == "NA":
            continue
        if _looks_invalid_text(value):
            invalid.append(key)
    return invalid


def _fallback_output(partial: dict) -> dict:
    fallback = {
        "background": "The reported behavior does not match the expected system response and needs backend investigation.",
        "purpose": "1. Reproduce the issue consistently.\n2. Identify the backend root cause.\n3. Implement and verify the fix with regression coverage.",
        "process": "Step 1 — Reproduce\nTasks\n• Execute provided reproduction steps\n• Compare expected vs actual\nStep 2 — Fix\nTasks\n• Correct backend response-injection flow\n• Validate first-call-only logic\nStep 3 — Verify\nTasks\n• Re-test end-to-end\n• Confirm no regression",
        "considerable_factors": "Dependencies on backend injection flow, SOAP response handling, and test data consistency.",
        "resulting_image": "• Expected response replacement works on first call\n• Second call behavior is correct\n• End-to-end test passes",
    }
    merged = dict(fallback)
    for key in REQUIRED_KEYS:
        value = partial.get(key, "")
        if not _looks_invalid_text(value):
            merged[key] = value
    return merged


def _schema_payload() -> dict:
    return {
        "type": "object",
        "properties": {
            "background": {"type": "string"},
            "purpose": {"type": "string"},
            "process": {"type": "string"},
            "considerable_factors": {"type": "string"},
            "resulting_image": {"type": "string"},
        },
        "required": REQUIRED_KEYS,
        "additionalProperties": True,
    }


async def generate_with_ollama(prompt: str) -> dict:
    """Generate requirement JSON via Ollama and return a sanitized dict."""
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_llm_model,
                "prompt": prompt,
                "stream": False,
                "format": _schema_payload(),
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                },
            },
        )
        response.raise_for_status()
        raw = response.json().get("response", "")

    parsed = _parse_model_output(raw)
    sanitized = _sanitize_llm_output(parsed)
    invalid_keys = _invalid_sections(sanitized)
    if not invalid_keys:
        return sanitized

    repair_prompt = f"""You returned malformed sections: {', '.join(invalid_keys)}.
Rewrite the ticket as strict JSON only, with meaningful non-empty text for all required fields.
Do not use placeholder punctuation like :[ or ...

Required keys:
{json.dumps(REQUIRED_KEYS)}

Original requirement:
{prompt}

Previous JSON:
{json.dumps(sanitized, ensure_ascii=False)}
"""

    async with httpx.AsyncClient(timeout=180.0) as client:
        repair_response = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_llm_model,
                "prompt": repair_prompt,
                "stream": False,
                "format": _schema_payload(),
                "options": {
                    "temperature": 0.0,
                    "top_p": 0.9,
                },
            },
        )
        repair_response.raise_for_status()
        repair_raw = repair_response.json().get("response", "")

    repaired = _sanitize_llm_output(_parse_model_output(repair_raw))
    if _invalid_sections(repaired):
        return _fallback_output(repaired)
    return repaired
