import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from idna import encode
from middlewares.error_logging import ErrorLoggingMiddleware
from routers.vision import router as vision_router
from routers.recipe import router as recipe_router
logging.basicConfig(filename="myapp.log", encoding="utf-8", level=logging.DEBUG,)

logger = logging.getLogger(__name__)

app = FastAPI()



@app.get("/health")
def health():
    return "hello"

app.include_router(vision_router)
app.include_router(recipe_router)

app.add_middleware(ErrorLoggingMiddleware)
app.add_middleware(CORSMiddleware,
                   allow_origins=["*"],
                   allow_methods=["GET","POST","OPTIONS"],
                   allow_headers=["*"]
                   )

# if __name__ == "__main__":
#     import uvicorn
#     logger.debug("Hello")
#     uvicorn.run("main:app",host="0.0.0.0",port=8000, reload=True)
    