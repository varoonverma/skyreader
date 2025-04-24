# app/main.py
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router

load_dotenv()
app = FastAPI()

# Global exception handler
@app.exception_handler(Exception)
async def all_exceptions(request: Request, exc: Exception):
    return JSONResponse(status_code=502, content={"detail": str(exc)})

app.include_router(router)