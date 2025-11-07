import json
from providers.prompts import SYSTEM_PREFIX, TASK_PREFIX


def expand_small_to_full(small_obj: dict, constraints: dict) -> dict:
    # small_obj: {"r":[{"t","tm","m","sv","st"} x5]}
    r_small = small_obj.get("r") or []
    allowed = {m.lower() for m in (constraints.get("allowed_methods") or []) if isinstance(m, str)}
    max_minutes = constraints.get("max_minutes")

    recipes = []
    for it in r_small:
        title  = it.get("t", "").strip()
        tm     = int(it.get("tm", 0)) if isinstance(it.get("tm"), int) else 0
        method = (it.get("m") or "").strip().lower()
        sv     = int(it.get("sv", 1)) if isinstance(it.get("sv"), int) else 1
        steps  = [s.strip() for s in (it.get("st") or []) if isinstance(s, str) and s.strip()]

        # hậu kiểm method
        if allowed:
            if method not in allowed:
                method = next(iter(allowed))  # ép về giá trị allowed đầu tiên

        # hậu kiểm time
        if isinstance(max_minutes, int) and max_minutes > 0 and tm > max_minutes:
            tm = max_minutes

        recipes.append({
            "title": title,
            "time_minutes": tm,
            "difficulty": "easy" if tm <= 25 else "medium",
            "method": method,
            "servings": sv,
            "steps": steps,
            "missing": [],
            "substitutions": [],
            "nutrition_per_serving": {"kcal": None, "protein_g": None, "carb_g": None, "fat_g": None},
            "reasons": ["Meets time & method constraints"]
        })
    return {"recipes": recipes}

def build_input_text(ingredients_list: list[dict], constraints_block: str) -> str:
    return (
        SYSTEM_PREFIX + "\n" +
        TASK_PREFIX   + "\n" +
        "SCHEMA:r->[t,tm,m,sv,st]\n" +         # nhắc schema rút gọn dạng ngắn
        "INGREDIENTS:" +
        json.dumps(ingredients_list, ensure_ascii=False, separators=(",",":")) + "\n" +
        constraints_block
    )
    