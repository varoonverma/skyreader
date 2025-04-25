# app/main.py
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import os
from contextlib import asynccontextmanager

from app.api.routes import router
from app.exception.exceptions import SkyReaderError
from app.service.local_parser import LocalModelParser
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()



# Initialize application with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize resources
    logging.info("Starting SkyReader API")

    # Initialize local model if enabled
    if os.getenv("USE_LOCAL_MODEL").lower() == "true":
        model_path = os.getenv("LOCAL_MODEL_PATH")
        logging.info(f"Initializing local model from {model_path}")
        try:
            LocalModelParser.initialize(model_path)
            logging.info("Local model initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize local model: {e}")
            # Don't fail startup, as we can still use remote models

    yield  # App runs here

    # Shutdown: cleanup resources
    logging.info("Shutting down SkyReader API")

app = FastAPI(
    title="SkyReader API",
    description="Parser for IATA Type B aviation messages",
    lifespan=lifespan
)

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

# Include API routes
app.include_router(router)