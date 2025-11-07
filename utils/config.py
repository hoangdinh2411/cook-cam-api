import os 
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY= os.getenv("OPENAI_API_KEY")
OPENAI_VISION_MODEL= os.getenv("OPENAI_VISION_MODEL")
OPENAI_RECIPES_MODEL= os.getenv("OPENAI_RECIPES_MODEL")

MAX_IMAGE_BYTES= int(os.getenv("MAX_IMAGE_BYTES"))
REDIS_URL= os.getenv("REDIS_URL")

VISION_CACHE_TTL= int(os.getenv("VISION_CACHE_TTL"))
RECIPES_CACHE_TTL= int(os.getenv("RECIPES_CACHE_TTL"))