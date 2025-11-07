import json
from fastapi import APIRouter, HTTPException
from cache.keys import recipes_key
from cache.redis_client import get_redis
from models.recipe import RecipesIn, RecipesOut
from providers.language import enforce_language
from providers.openai_client import recipes_from_ingredients, translate_recipes_json
from utils.config import RECIPES_CACHE_TTL


router = APIRouter()

@router.post("/recipes", response_model=RecipesOut)
async def get_recipes_from_ingredients(payload:RecipesIn):
    """
    Generate recipes from confirmed ingredients and user constraints.

    Flow:
      1) Canonicalize input into plain dicts (Pydantic models -> dicts).
      2) Try cache by canonical key.
        Check if language is correct, or not , translating cached recipes to the language user selected
      3) On cache miss, call OpenAI (JSON mode) to generate 3–5 recipes.
      4) Store result in cache and return it.
    """
    
    ingredients_as_dict= [ingredient.model_dump() for ingredient in payload.ingredients]
    constraints_as_dict  = payload.constraints.model_dump()
    target_code = (constraints_as_dict.get("output_lang") or "en").lower()
    
    cache_client = await get_redis()
    key = await recipes_key(ingredients_as_dict, constraints_as_dict)
    
    cached_text = await cache_client.get(key)
    if cached_text :
      try:
          print("has cached")
          if not enforce_language(cached_text,target_code=target_code):
            return await translate_recipes_json(cached_text, target_code)
          else:
            return json.loads(cached_text)
      except Exception:
        pass
    print("finding new ")
    
    try:
      provider_result = await recipes_from_ingredients(ingredients_as_dict, constraints_as_dict)
    except Exception as exc:
      raise HTTPException(status_code=503, detail=f"Recipes provider error: {exc}")
    
    if not isinstance(provider_result,dict):
      raise HTTPException(status_code=502, detail=f"Bad provider result (not JSON object)")
    
    recipes_list = provider_result.get("recipes") or []
    if not isinstance(recipes_list,list):
      recipes_list=[]
    response_body = {"recipes": recipes_list}
    await cache_client.setex(key, RECIPES_CACHE_TTL, json.dumps(response_body, ensure_ascii=False))
    
    return response_body