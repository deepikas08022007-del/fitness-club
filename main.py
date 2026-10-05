"""FastAPI application factory for FitBuddy."""

import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import Settings, get_settings
from app.routers import api, pages
from app.services.gemini_service import GeminiService

STATIC_DIR = Path(__file__).resolve().parent / "static"
RATE_LIMITED_PATHS = ("/api/plan", "/generate")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("fitbuddy")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = settings
        app.state.gemini = GeminiService(settings)
        mode = "DEMO (no API key)" if app.state.gemini.demo_mode else f"Gemini {settings.gemini_model}"
        logger.info("%s v%s started in %s mode", settings.app_name, __version__, mode)
        yield

    app = FastAPI(
        title=f"{settings.app_name} - AI Fitness Plan Generator",
        description="Personalised workout and nutrition plans powered by Gemini models.",
        version=__version__,
        lifespan=lifespan,
    )
    # Available even before lifespan runs (e.g. when used without a context manager).
    app.state.settings = settings
    app.state.gemini = GeminiService(settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    hits: dict[str, deque[float]] = defaultdict(deque)

    @app.middleware("http")
    async def security_and_rate_limit(request: Request, call_next):
        if request.url.path in RATE_LIMITED_PATHS and request.method == "POST":
            ip = request.client.host if request.client else "unknown"
            now = time.monotonic()
            window = hits[ip]
            while window and now - window[0] > 60:
                window.popleft()
            if len(window) >= settings.rate_limit_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please wait a minute and try again."},
                )
            window.append(now)
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError):
        problems = []
        for err in exc.errors():
            field = ".".join(str(p) for p in err["loc"] if p != "body")
            problems.append(f"{field}: {err['msg']}")
        return JSONResponse(
            status_code=422,
            content={"detail": "Please check your inputs. " + "; ".join(problems)},
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(_: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Something went wrong on our side."})

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.include_router(api.router)
    app.include_router(pages.router)
    return app


app = create_app()
