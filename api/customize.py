from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import json
import re

from openai import OpenAI

router = APIRouter(prefix="/api", tags=["customize"])


class CustomizeRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    tone: str = Field("formal", description="formal | informal")
    include_charts: bool = False
    length: str = Field("short", description="short | long")


class CustomizeResponse(BaseModel):
    text: str
    chart_data: Optional[List[Dict[str, Any]]] = None


def _build_system_prompt(tone: str, length: str, include_charts: bool) -> str:
    tone_map = {
        "formal": "Use a professional and concise tone.",
        "informal": "Use a friendly and conversational tone.",
    }
    length_map = {
        "short": "Keep the response brief (3-5 sentences).",
        "long": "Provide a detailed response (6-12 sentences).",
    }

    tone_instr = tone_map.get(tone.lower(), tone_map["formal"]) 
    length_instr = length_map.get(length.lower(), length_map["short"])
    chart_instr = (
        "Also summarize up to 5 key categories with numeric values appropriate for a simple chart. "
        "At the very end of the message, output a single line starting with CHART_JSON= followed by a JSON array \n"
        "like [{\"label\":\"Category\",\"value\":12}], or null if no chart is needed."
        if include_charts
        else "At the very end of the message, output a single line: CHART_JSON=null"
    )

    return (
        "You are an assistant for a website that customizes responses based on user preferences.\n"
        f"{tone_instr}\n"
        f"{length_instr}\n"
        f"{chart_instr}\n"
        "Do not wrap the CHART_JSON line in code fences."
    )


def _extract_chart_json(text: str) -> (str, Optional[List[Dict[str, Any]]]):
    # Look for a trailing line like: CHART_JSON=...
    chart_data = None
    pattern = r"CHART_JSON\s*=\s*(.+)"
    match = re.search(pattern, text.strip(), re.IGNORECASE)
    if match:
        tail = match.group(0)
        json_part = match.group(1).strip()
        # Remove the CHART_JSON line from the main text
        main_text = text.replace(tail, "").strip()
        if json_part.lower() != "null":
            try:
                chart_data = json.loads(json_part)
            except Exception:
                chart_data = None
        return main_text.strip(), chart_data
    return text.strip(), None


@router.post("/customize", response_model=CustomizeResponse)
async def customize(req: CustomizeRequest) -> CustomizeResponse:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured on the server")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    system_prompt = _build_system_prompt(req.tone, req.length, req.include_charts)

    try:
        client = OpenAI(api_key=api_key)
        # Use Chat Completions for broad compatibility
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.prompt},
            ],
            temperature=0.7,
        )
        content = completion.choices[0].message.content or ""
        text, chart = _extract_chart_json(content)
        return CustomizeResponse(text=text, chart_data=chart)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")
