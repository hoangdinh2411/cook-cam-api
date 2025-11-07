from pydantic import BaseModel

from models.recipe import IngredientsDetected


class VisionIn(BaseModel):
    imageBase64: str    
    
class VisionOut(BaseModel):
    ingredients: list[IngredientsDetected]