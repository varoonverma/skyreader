import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.exceptions import SkyReaderError
from app.parser.local import LocalModelParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s [%(levelname)s] %(message)s",
)

# Load .env
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("🛫 Starting SkyReader API")

    # Optional torch optimizations
    if os.getenv("OPTIMIZE_TORCH", "false").lower() == "true":
        try:
            import torch

            logging.info("🔧 Applying PyTorch performance tweaks")
            torch.set_num_threads(int(os.getenv("TORCH_NUM_THREADS", "4")))
            if hasattr(torch.backends, "cuda"):
                torch.backends.cuda.matmul.allow_tf32 = True
            if hasattr(torch.backends, "cudnn"):
                torch.backends.cudnn.allow_tf32 = True
                torch.backends.cudnn.benchmark = True
        except ImportError:
            logging.warning("⚠️ PyTorch not installed; skipping optimizations")

    # Initialize local LLM if requested
    if os.getenv("USE_LOCAL_MODEL", "false").lower() == "true":
        base = os.getenv("LOCAL_BASE_MODEL_PATH")
        logging.info(f"📥 Initializing LocalModelParser(base={base})")
        try:
            LocalModelParser.initialize(base_model_path=base)
            logging.info("✅ Local model initialized")
        except Exception as e:
            logging.error("❌ Local model failed to initialize: %s", e)

    yield

    logging.info("🛬 Shutting down SkyReader API")


app = FastAPI(
    title="SkyReader API",
    description="Parse IATA Type B (MVT/MVA/DIV) messages into JSON",
    lifespan=lifespan,
)


@app.exception_handler(SkyReaderError)
async def skyreader_error(request: Request, exc: SkyReaderError):
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid request", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def all_exceptions(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500, content={"detail": f"Unexpected error: {exc}"}
    )


app.include_router(router)