import json
import logging
from fastapi import APIRouter, HTTPException
from cache.keys import vision_key
from cache.redis_client import get_redis
from models.vision import VisionIn
from providers.openai_client import vision_dataurl_to_ingredients
from utils.utils import size_fromm_b64, split_data_url,dedup_and_merge
from utils.config import MAX_IMAGE_BYTES, VISION_CACHE_TTL

logger = logging.getLogger(__name__)
router = APIRouter()
ALLOW_IMAGE_MIMES={
    "image/png",
    "image/jpg",
    "image/webp",
    "image/jpeg"
}


def validate_image_mime(m:str):
    if m is None:
        logger.debug("Missing mime")
        raise HTTPException(status_code=400,
                            detail="Missing mime")
    if m not in ALLOW_IMAGE_MIMES:
        value = m or "unknown"

        logger.debug(f"Unsupported media type: {value}. ")
        raise HTTPException(status_code=415,
                            detail=f"Unsupported media type: {value}. "
                            f"Allow: {', '.join(sorted(ALLOW_IMAGE_MIMES))}")
    

@router.post('/vision')
async def vision (payload:VisionIn):
    logger.debug(f"mime is:")
    try: 
        mime, b64= split_data_url(payload.imageBase64)
    except Exception as e:
        raise HTTPException(400, detail=e)
    
    validate_image_mime(mime)
    if size_fromm_b64(b64) > int(MAX_IMAGE_BYTES,0):
        raise HTTPException(400, detail="Image too large")
    
    key= await vision_key(mime, b64)
    r= await get_redis()
    if r:
        cached = await r.get(key)
        print('cached',cached)
        if cached:
            try:
                data= json.loads(cached)
                return data
            except Exception:
                await r.delete(key)

    data_url = f"data:image/{mime};base64,{b64}"    
    print("do a new vision")
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
        
        