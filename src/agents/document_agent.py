"""
src/agents/document_agent.py
Extracts field values from PDF/text documents by calling the local Ollama model.

Design principles:
- No hardcoded field names or categories — works for any field defined in schema
- JSON schema retry: if LLM returns invalid JSON, retries once with a stricter prompt
- Every call returns an ExtractionResult with the source span (where in the doc it found the value)
- Model name comes from config.yaml — not hardcoded
"""
from __future__ import annotations
import json
import re
import subprocess
import shutil
from pathlib import Path
import requests
from src.config import cfg
from src.models import ExtractionResult


# ── Prompt templates ─────────────────────────────────────────────────────────
# Kept deliberately SHORT — fewer tokens = faster inference on local hardware.

SYSTEM_PROMPT = (
    "You extract product specification values from technical documents. "
    "Return ONLY valid JSON. Never explain. If unsure, return null."
)

USER_PROMPT_TEMPLATE = """\
Extract "{field_name}" ({field_type}, unit: {field_unit}, range: {field_min}–{field_max}{field_enum_hint}) from:
---
{text_chunk}
---
JSON only: {{"value": <value_or_null>, "source_span": "<quote_from_text>", "unit_found": "<unit_or_null>"}}"""

USER_PROMPT_WITH_CONTEXT = """\
Extract "{field_name}" ({field_type}, unit: {field_unit}, range: {field_min}–{field_max}{field_enum_hint}).
Reference examples: {rag_context}
Document: ---
{text_chunk}
---
JSON only: {{"value": <value_or_null>, "source_span": "<quote_from_text>", "unit_found": "<unit_or_null>"}}"""


# ── Helper: call Ollama ───────────────────────────────────────────────────────

def _call_ollama_subprocess(full_prompt: str) -> str:
    """
    Call Ollama via stdin pipe — same as: echo "prompt" | ollama run model
    Using stdin because long multi-line prompts are mangled by Windows CLI args.
    Model name and exe path come from config.yaml — not hardcoded.
    """
    exe = cfg.ollama.ollama_exe.replace("/", "\\") if cfg.ollama.ollama_exe else ""
    if not exe or not Path(exe).exists():
        exe = shutil.which("ollama") or ""
    if not exe:
        raise FileNotFoundError(
            "ollama executable not found. Set ollama.ollama_exe in config.yaml"
        )

    # Use stdin pipe — reliable for any prompt length/content on Windows
    subprocess_timeout = max(cfg.ollama.timeout_seconds, 300)  # at least 5min for slow machines
    result = subprocess.run(
        [exe, "run", cfg.ollama.text_model],
        input=full_prompt,          # ← pipe prompt via stdin, NOT as CLI arg
        capture_output=True,
        text=True,
        timeout=subprocess_timeout,
        encoding="utf-8",
        errors="replace",
    )
    output = result.stdout.strip()
    if not output and result.stderr:
        raise ValueError(f"Ollama CLI error: {result.stderr[:300]}")
    return output


def _call_ollama_http(full_prompt: str) -> str:
    """
    Call Ollama via HTTP /api/generate.
    Fast path when Ollama is warm — falls back to subprocess if it times out.
    """
    url = f"{cfg.ollama.base_url}/api/generate"
    payload = {
        "model": cfg.ollama.text_model,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 300},
    }
    # Use a shorter timeout for HTTP so we fail fast and fall back to subprocess
    http_timeout = min(cfg.ollama.timeout_seconds, 45)
    resp = requests.post(url, json=payload, timeout=http_timeout)

    if resp.status_code == 404:
        raise ValueError(f"Model '{cfg.ollama.text_model}' not found. Run: ollama pull {cfg.ollama.text_model}")
    if resp.status_code != 200:
        raise ValueError(f"Ollama API error {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    if "response" not in data:
        raise ValueError(f"Unexpected response format: {str(data)[:200]}")
    return data["response"].strip()


def _call_ollama(prompt: str, system: str) -> str:
    """
    Call the Ollama model with system + user prompt.
    Strategy: try HTTP API first (fast when model is warm),
              fall back to subprocess CLI (reliable, works even when API hangs).
    Model name comes from config.yaml — not hardcoded.
    """
    full_prompt = f"{system}\n\n{prompt}"

    # Try HTTP first (faster when Ollama is warm)
    try:
        return _call_ollama_http(full_prompt)
    except requests.exceptions.ReadTimeout:
        print("    [INFO] HTTP API timed out, falling back to subprocess CLI...", flush=True)
    except requests.exceptions.ConnectionError:
        print("    [INFO] HTTP API unavailable, falling back to subprocess CLI...", flush=True)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise  # model not found — subprocess won't help either
        print(f"    [INFO] HTTP API error ({e}), falling back to subprocess...", flush=True)

    # Subprocess fallback — guaranteed to work if 'ollama run' works in terminal
    return _call_ollama_subprocess(full_prompt)



def _parse_json_response(raw: str) -> dict:
    """
    Parse the LLM's JSON response.
    Handles cases where the model wraps JSON in markdown code fences.
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()

    # Find the first { ... } block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    return json.loads(cleaned)


def _build_field_prompt_args(field_name: str, field_def: dict) -> dict:
    enum_vals = field_def.get("enum")
    enum_hint = f", options: {enum_vals}" if enum_vals else ""
    return {
        "field_name":      field_name,
        "field_type":      field_def.get("type", "string"),
        "field_unit":      field_def.get("unit", "N/A"),
        "field_min":       field_def.get("min", "any"),
        "field_max":       field_def.get("max", "any"),
        "field_enum_hint": enum_hint,
    }


# ── Public API ────────────────────────────────────────────────────────────────

def extract_from_text(
    field_name: str,
    field_def: dict,
    text_chunk: str,
    page_no: int | None = None,
    source_file: str = "",
) -> ExtractionResult:
    """
    Extract a single field value from a text chunk.
    Returns ExtractionResult — value is None if not found.
    """
    args = _build_field_prompt_args(field_name, field_def)
    args["text_chunk"] = text_chunk
    prompt = USER_PROMPT_TEMPLATE.format(**args)

    try:
        raw = _call_ollama(prompt, SYSTEM_PROMPT)
        parsed = _parse_json_response(raw)
        extracted_value = parsed.get("value")
        # Treat explicit null/None from LLM as not found
        return ExtractionResult(
            value=extracted_value,
            source_span=parsed.get("source_span", ""),
            unit_found=parsed.get("unit_found"),
            page_number=page_no,
            agent="document_agent",
            raw_llm_response=raw,
        )
    except json.JSONDecodeError as e:
        # Bad JSON — retry once with a stricter prompt
        strict_prompt = prompt + "\n\nCRITICAL: Return ONLY the JSON object on one line. No explanation. No markdown."
        try:
            raw2 = _call_ollama(strict_prompt, SYSTEM_PROMPT)
            parsed2 = _parse_json_response(raw2)
            return ExtractionResult(
                value=parsed2.get("value"),
                source_span=parsed2.get("source_span", ""),
                unit_found=parsed2.get("unit_found"),
                page_number=page_no,
                agent="document_agent",
                raw_llm_response=raw2,
            )
        except Exception as e2:
            error_msg = f"JSON retry failed: {e2} | original raw: {str(raw)[:200]}"
            print(f"    [AGENT WARN] {error_msg}")
            return ExtractionResult(value=None, agent="document_agent", raw_llm_response=error_msg)
    except (requests.RequestException, ValueError, subprocess.TimeoutExpired, OSError) as e:
        # Network error, model not found, timeout, subprocess error — surface clearly
        error_msg = f"{type(e).__name__}: {str(e)[:200]}"
        print(f"    [AGENT ERROR] {error_msg}")
        return ExtractionResult(value=None, agent="document_agent", raw_llm_response=error_msg)


def extract_from_text_with_rag_context(
    field_name: str,
    field_def: dict,
    text_chunk: str,
    rag_documents: list[str],
    page_no: int | None = None,
) -> ExtractionResult:
    """
    Extract with RAG context — similar products are injected as few-shot grounding.
    Used when direct extraction failed and RAG retrieval found similar products.
    """
    rag_context = "\n".join(f"- {d}" for d in rag_documents[:3])
    args = _build_field_prompt_args(field_name, field_def)
    args["text_chunk"] = text_chunk
    args["rag_context"] = rag_context
    prompt = USER_PROMPT_WITH_CONTEXT.format(**args)

    try:
        raw = _call_ollama(prompt, SYSTEM_PROMPT)
        parsed = _parse_json_response(raw)
        return ExtractionResult(
            value=parsed.get("value"),
            source_span=parsed.get("source_span", ""),
            unit_found=parsed.get("unit_found"),
            page_number=page_no,
            agent="document_agent+rag",
            raw_llm_response=raw,
        )
    except Exception as e:
        return ExtractionResult(
            value=None,
            agent="document_agent+rag",
            raw_llm_response=str(e),
        )
