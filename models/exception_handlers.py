from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


async def http_exception_handler(request:Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={
        "success":False,
        "error":exc.detail
    })

async def general_exception_handler(request:Request, exc: Exception):
    return JSONResponse(status_code=500, content={
        "success":False,
        "error":exc.detail or "Internal server error"
    })
async def value_exception_handler(request:Request, exc: ValueError):
    return JSONResponse(status_code=400, content={
        "success":False,
        "error":f"Invalid value: {str(exc)}"
    })