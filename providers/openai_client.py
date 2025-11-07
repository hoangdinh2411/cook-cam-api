
import asyncio
import json
import random
from typing import Optional
import unicodedata
from openai import APIError, OpenAI, RateLimitError

from providers.helper import build_input_text, expand_small_to_full
from providers.prompts import SYSTEM_PREFIX, TASK_PREFIX
from providers.schema import RECIPE_SCHEMA
from utils.config import OPENAI_API_KEY, OPENAI_RECIPES_MODEL, OPENAI_VISION_MODEL


_client = OpenAI(api_key=OPENAI_API_KEY)
async def chat_json(messages,model:str, 
    max_tokens: int = 900,
    response_format: dict | None = None,):
    if response_format is None:
        response_format = {"type": "json_object"}

    for i in range(4):
        try:
            r = _client.chat.completions.create(
                model=model,
                temperature=0,
                top_p=0,
                n=1,
                response_format=response_format,   # <— supported on newer models/SDK
                max_tokens=max_tokens,             # <— NOT `max_token`
                messages=messages,
            )
            txt = r.choices[0].message.content or "{}"
            try:
                return json.loads(txt)
            except json.JSONDecodeError:
                return {}
        except (RateLimitError, APIError):
            if i == 3:
                raise
            await asyncio.sleep((2 ** i) + random.uniform(0, 0.4))
        except Exception:
            if i == 3:
                return {}
            await asyncio.sleep((2 ** i) + random.uniform(0, 0.4))
    return {}
            
async def vision_dataurl_to_ingredients(data_url:str):
    msgs=[
        {
            "role":"system",
            "content":"Only list ingredients that are visibly present. Do NOT invent generic items like oil/spices if not visible."
        },
        {
            "role":"user",
            "content":[
                {
                    "type":"text",
                    "text":"Return ONLY JSON: {\"ingredients\":[{\"name\":\"string\",\"confidence\":0..1,\"approx_qty_grams\":number|null}] }"
                },
                {
                    "type":"image_url",
                    "image_url":{
                        "url":data_url
                    }
                }
            ]
        }
    ]
    return await chat_json(msgs, OPENAI_VISION_MODEL)

def _norm(s: str) -> str:
    return unicodedata.normalize("NFKC", s or "").strip()

def build_constraints_block(
    *,
    cuisine: Optional[str] = None,
    max_minutes: Optional[int] = None,
    servings: Optional[int] = None,
    allowed_methods: Optional[list[str]] = None,
    diet: Optional[str] = None,
    allergies: Optional[list[str]] = None,
    output_lang: Optional[str] = None,
) -> str:
    cons = {
        "cuisine": _norm(cuisine),
        "max_minutes": max_minutes,
        "servings": servings,
        "allowed_methods": [m.strip().lower() for m in (allowed_methods or []) if m and m.strip()],
        "diet": _norm(diet),
        "allergies": [a.strip().lower() for a in (allergies or []) if a and a.strip()],
        "output_lang": _norm(output_lang),  # <-- MỚI
    }
    cons = {k: v for k, v in cons.items() if v not in (None, "", [])}
    guide = []
    if "max_minutes" in cons:
        guide.append("All recipes must finish within max_minutes.")
    if "allowed_methods" in cons:
        guide.append("Use only the allowed methods.")
    if "diet" in cons or "allergies" in cons:
        guide.append("Respect diet and avoid allergens.")
    if "output_lang" in cons:
        guide.append("All text (titles, steps, reasons) must be written in the language specified by output_lang.")
        guide.append("Keep proper nouns; do not mix languages.")
    return (
        "CONSTRAINTS_GUIDE:" + " ".join(guide) + "\n" +
        "CONSTRAINTS:" + json.dumps(cons, ensure_ascii=False, separators=(",",":"))
    )
    
    
async def translate_recipes_json(full_obj:dict, lang_code:str)->dict:
    messages=[
        {
            "role":"system",
            "content":"You are a precise translator. Return ONLY JSON. Keep keys, arrays, numbers unchanged."
        },
        {
            "role":"user",
            "content": f"Translate all text values in this JSON to language code '{lang_code}'. "
            "Do not change keys, structure, or numbers. Return ONLY the JSON.\n" +
            json.dumps(full_obj, ensure_ascii=False, separators=(',',':'))
        }

    ]  
    
    r= _client.chat.completions.create(
        model=OPENAI_RECIPES_MODEL,
        messages=messages,
        response_format={"type":"json_object"},
        temperature=0,
        top_p=0,
        max_tokens=900
    )
    
    try:
        return json.loads(r.choices[0].message.content or {})
    except json.JSONDecodeError:
        raise
    

async def recipes_from_ingredients(ingredients_list:list[dict],constraints_dict:dict)->dict:
    """
    Convert confirmed ingredients + constraints into EXACTLY 5 recipes.
    Always returns a dict per strict JSON schema.

    Input (ví dụ):
    ingredients_list = [{"name": "gà", "qty_grams": 400}, ...]
    constraints_dict = {
        "diet": "regular|keto|vegetarian|...",
        "allergies": ["peanut", ...],
        "max_minutes": 30,
        "servings": 2,
        "cuisine": "vietnamese|japanese|...",
        "allowed_methods": ["chiên","hấp"]   # (optional) ràng buộc phương pháp
    }

    Output schema:
    {
      "recipes": [{
        "title": str,
        "time_minutes": int,
        "difficulty": "easy" | "medium",
        "method": "chiên" | "hấp" | "xào" | "nướng" | "...",
        "servings": int,
        "missing": [str],                              # nguyên liệu cần thêm (nếu có)
        "substitutions": [{"for": str, "use": str}],   # gợi ý thay thế
        "steps": [str],                                 # các bước ngắn gọn
        "nutrition_per_serving": {
            "kcal": number|null, "protein_g": number|null,
            "carb_g": number|null, "fat_g": number|null
        },
        "reasons": [str]   # vì sao món này phù hợp với ingredients/constraints
      } x 5]
    }
    """
    # ===== 1) SYSTEM PROMPT =====
    constraints_block = build_constraints_block(**constraints_dict)
    input_text = build_input_text(ingredients_list, constraints_block)
    
    # 1) Thử Responses API (nếu SDK hỗ trợ response_format)
    try:
        resp = _client.responses.create(
            model=OPENAI_RECIPES_MODEL,                 # ví dụ "gpt-4o-mini"
            input=input_text,
            response_format={"type": "json_schema", "json_schema": RECIPE_SCHEMA},
            max_output_tokens=900,
            temperature=0, top_p=0,
        )
        data = json.loads(resp.output_text or "{}")
        return expand_small_to_full(data, constraints_dict) if isinstance(data, dict) else {}
        
    except TypeError as e:
        # Trường hợp phổ biến: "Responses.create() got an unexpected keyword argument 'response_format'"
        # => Fallback sang Chat Completions (có hỗ trợ response_format)
        if "response_format" not in str(e):
            raise

    # 2) Fallback: Chat Completions (luôn hoạt động với response_format)
    messages = [
        {"role": "system", "content": SYSTEM_PREFIX},
        {"role": "user",   "content": input_text},
    ]
    r = _client.chat.completions.create(
        model=OPENAI_RECIPES_MODEL,
        messages=messages,
        response_format={"type": "json_schema", "json_schema": RECIPE_SCHEMA},
        temperature=0, top_p=0,
        max_tokens=900
    )
    txt = r.choices[0].message.content or "{}"
    try:
        data = json.loads(txt)
    except json.JSONDecodeError:
        data = {}
    return expand_small_to_full(data, constraints_dict) if isinstance(data, dict) else {}