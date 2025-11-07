from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.vision import router as vision_router
from routers.recipe import router as recipe_router

app = FastAPI()

app.add_middleware(CORSMiddleware,
                   allow_origins=["*"],
                   allow_methods=["GET","POST","OPTIONS"],
                   allow_headers=["*"]
                   )

@app.get("/")
def health():
    return "hello"

app.include_router(vision_router)
app.include_router(recipe_router)
