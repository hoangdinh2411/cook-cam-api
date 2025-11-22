import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from middlewares.error_logging import ErrorLoggingMiddleware
from models.exception_handlers import general_exception_handler, http_exception_handler, value_exception_handler
from routers.vision import router as vision_router
from routers.recipe import router as recipe_router
logging.basicConfig(filename="myapp.log", encoding="utf-8", level=logging.DEBUG,)

logger = logging.getLogger(__name__)

app = FastAPI()



@app.get("/health")
def health():
    return "hello"
app.add_middleware(ErrorLoggingMiddleware)
app.add_exception_handler(HTTPException,http_exception_handler)
app.add_exception_handler(ValueError,value_exception_handler)
app.add_exception_handler(Exception,general_exception_handler)

app.include_router(vision_router)
app.include_router(recipe_router)

app.add_middleware(CORSMiddleware,
                   allow_origins=["*"],
                   allow_methods=["GET","POST","OPTIONS"],
                   allow_headers=["*"]
                   )

# if __name__ == "__main__":
#     import uvicorn
#     logger.debug("Hello")
#     uvicorn.run("main:app",host="0.0.0.0",port=8000, reload=True)
    