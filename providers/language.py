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
    samples = []
    for r in full_obj.get("recipes", []):
        t = r.get("title")
        if isinstance(t, str) and t.strip():
            samples.append(t.strip())
        for s in r.get("steps", [])[:4]:
            if isinstance(s, str) and s.strip():
                samples.append(s.strip())
        if len(samples) >= 8:
            break
    if not samples:
        return True
    hits = sum(1 for s in samples if _is_lang(s, target_code))
    ratio = hits / len(samples)
    # debug:
    # print(f"[lang] target={target_code} hits={hits}/{len(samples)} ratio={ratio:.2f} samples={samples[:3]}")
    return ratio >= 0.6



  