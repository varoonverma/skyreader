# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv
from app.api.routes import router
from app.exception.exceptions import SkyReaderError

load_dotenv()
app = FastAPI()

# Custom exception handlers
@app.exception_handler(SkyReaderError)
async def skyreader_exception_handler(request: Request, exc: SkyReaderError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid request parameters", "errors": exc.errors()},
    )

# Global exception handler for unexpected errors
@app.exception_handler(Exception)
async def all_exceptions(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected error occurred: {str(exc)}"},
    )

app.include_router(router)