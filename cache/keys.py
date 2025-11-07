import hashlib
import json
from typing import Optional
import unicodedata


async def vision_key(mine:str, b64:str)->str:
    h= hashlib.sha1(f"{mine}:{b64}".encode()).hexdigest()
    return f"v1:vision:{h}"

RECIPES_NAMESPACE = "v1"

def _norm_text(s: str) -> str:
    # chuẩn hoá unicode + lowercase + strip
    return unicodedata.normalize("NFKC", s).strip().lower()

def _round_qty(x: Optional[float]) -> Optional[float]:
    if x is None:
        return None
    try:
        # làm tròn về 1 chữ số thập phân để tránh nhiễu nhỏ từ OCR/ước lượng
        return round(float(x), 1)
    except Exception:
        return None

def _clean_ingredient(it: dict[str, any]) -> dict[str, any]:
    # chấp nhận các field phổ biến: name, approx_qty_grams, confidence, candidates
    name = _norm_text(str(it.get("name", "")))
    qty  = _round_qty(it.get("approx_qty_grams"))
    conf = it.get("confidence")
    try:
        conf = None if conf is None else round(float(conf), 3)
    except Exception:
        conf = None

    # candidates (nếu có) -> danh sách {name, score} đã chuẩn hoá & sort
    raw_cands = it.get("candidates") or []
    cands = []
    for c in raw_cands:
        try:
            cname = _norm_text(str(c.get("name", "")))
            score = c.get("score")
            score = None if score is None else round(float(score), 3)
            if cname:
                cands.append({"name": cname, "score": score})
        except Exception:
            continue
    # sort candidates theo (-score, name)
    cands.sort(key=lambda x: (-(x["score"] if x["score"] is not None else -1.0), x["name"]))

    out = {
        "name": name,
        "approx_qty_grams": qty,
        "confidence": conf,
    }
    if cands:
        out["candidates"] = cands
    return out

def _clean_constraints(c: dict[str, any]) -> dict[str, any]:
    if not isinstance(c, dict):
        return {}

    def _to_list_str(x) -> list[str]:
        if not x:
            return []
        if isinstance(x, str):
            x = [x]
        return sorted({_norm_text(str(i)) for i in x if str(i).strip()})

    out: dict[str, any] = {}

    if "diet" in c and c["diet"] is not None:
        out["diet"] = _norm_text(str(c["diet"]))

    if "allergies" in c:
        out["allergies"] = _to_list_str(c.get("allergies"))

    if "cuisine" in c and c["cuisine"] is not None:
        out["cuisine"] = _norm_text(str(c["cuisine"]))

    if "allowed_methods" in c:
        out["allowed_methods"] = _to_list_str(c.get("allowed_methods"))
    if "output_lang" in c:
        out["output_lang"] = _to_list_str(c.get("output_lang"))
        
    for k in ("max_minutes", "servings"):
        v = c.get(k)
        if isinstance(v, (int, float)):
            out[k] = int(v)

    return out

def _canonical_payload(ingredients_list: list[dict[str, any]], constraints_dict: dict[str, any]) -> dict[str, any]:
    cleaned_ings = [_clean_ingredient(i) for i in (ingredients_list or []) if isinstance(i, dict)]
    cleaned_ings.sort(key=lambda x: (x.get("name",""), x.get("approx_qty_grams") or -1))

    cleaned_constraints = _clean_constraints(constraints_dict or {})

    return {
        "ingredients": cleaned_ings,
        "constraints": cleaned_constraints
    }
async def recipes_key(ingredients_list: list[dict], constraints_dict: dict) -> str:
    """
    Tạo key cache ổn định cho (ingredients + constraints).
    Ví dụ key: recipes:v1:3a4f2e... (sha1)
    """
    canonical = _canonical_payload(ingredients_list, constraints_dict)

    canonical_json = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha1(canonical_json.encode("utf-8")).hexdigest()

    return f"recipes:v1:{digest}"