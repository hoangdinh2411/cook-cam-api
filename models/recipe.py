from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

class Candidate(BaseModel):
    name: str
    score: float = Field(..., ge=0, le=1)  # 0..1

class IngredientsDetected(BaseModel):
    name: str
    approx_qty_grams: Optional[float] = Field(default=None, ge=0)
    confidence: float = Field(..., ge=0, le=1)  # 0..1
    candidates: Optional[list[Candidate]] = None
    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str):
        if not v.strip():
            raise ValueError("name must not be empty")
        return v
    

class Constraints(BaseModel):
    diet: Optional[str] = "regular"    
    allergies: list[str] = []
    max_minutes: Optional[int] = 30
    servings: Optional[int] = 2
    cuisine: Optional[str] = "vietnamese"
    allowed_methods: list[str] = []
    output_lang: str
    
class Nutrition(BaseModel):
    """" Per serving nutrition. Use null for unknown values"""
    kcal:Optional[float]= None
    protein_g:Optional[float]= None
    carb_g: Optional[float]= None
    fat_b:Optional[float]= None
    
    
class Recipe(BaseModel):
    """"Structure of a generated recipe"""
    title: str
    time_minutes: int
    difficulty: Optional[Literal["easy","medium"]] ="easy"
    missing: list[str]=[] #items not available but needed
    substitutions: list[dict]=[] #suggested replacements
    steps: list[str] #ordered cooking steps
    nutrition_per_serving: Nutrition


class RecipesIn(BaseModel):
    """Request body for /recipe"""
    ingredients: list [IngredientsDetected]
    constraints: Constraints
    
class RecipesOut(BaseModel):
    """Response body for /recipes"""
    recipes:list[Recipe]
    
        
    
