import json
from fastapi import APIRouter, HTTPException
from cache.keys import vision_key
from cache.redis_client import get_redis
from models.vision import VisionIn
from providers.openai_client import vision_dataurl_to_ingredients
from utils.utils import size_fromm_b64, split_data_url,dedup_and_merge
from utils.config import MAX_IMAGE_BYTES, VISION_CACHE_TTL
router = APIRouter()


@router.post('/vision')
async def vision (payload:VisionIn):
    try: 
        mime, b64= split_data_url(payload.imageBase64)
    except Exception as e:
        raise HTTPException(400, e)
    
    if size_fromm_b64(b64) > int(MAX_IMAGE_BYTES,0):
        raise HTTPException(400, "Image too large")
    
    key= await vision_key(mime, b64)
    r= await get_redis()
    if r:
        cached = await r.get(key)
        print('cached',cached)
        if cached:
            try:
                data= json.loads(cached)
                return {"ingredients": data}
            except Exception:
                await r.delete(key)

    data_url = f"data:image/{mime};base64,{b64}"    
    try:
        result = await vision_dataurl_to_ingredients(data_url)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Vision provider error: {e}")

    if not isinstance(result, dict):
        raise HTTPException(status_code=502, detail="Bad provider result (not a JSON object)")
    items = result.get("ingredients") or []
    if not isinstance(items, list):
        items=[]
    resp = {"ingredients": items}    
    await r.setex(key, VISION_CACHE_TTL, json.dumps(resp, ensure_ascii=False))
    return resp
        
        