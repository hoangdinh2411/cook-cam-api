import json
from langdetect import detect, LangDetectException

def _is_lang(text: str, target_code: str) -> bool:
    try:
        code = detect(text) 
        return code == target_code
    except LangDetectException:
        return False

def enforce_language(full_obj: dict, target_code: str) -> bool:
    if not isinstance(full_obj, dict): return False
    hits, total = 0, 0
    for r in full_obj.get("recipes", []):
        for k in ("title",):
            v = r.get(k)
            if isinstance(v, str) and v.strip():
                total += 1
                hits += 1 if _is_lang(v, target_code) else 0
        for s in r.get("steps", []):
            if isinstance(s, str) and s.strip():
                total += 1
                if total <= 6:
                    hits += 1 if _is_lang(s, target_code) else 0
    return total == 0 or (hits / max(1, total) >= 0.6)



  