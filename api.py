"""JSON API endpoints (optional; the web UI uses the server-rendered routes)."""

from fastapi import APIRouter, HTTPException, Request

from app import __version__
from app.schemas import PlanResponse, UserProfile
from app.services.gemini_service import GeminiService, GeminiUnavailableError
from app.utils.health import compute_metrics

router = APIRouter(prefix="/api", tags=["api"])


def _service(request: Request) -> GeminiService:
    return request.app.state.gemini


@router.get("/health")
async def health(request: Request) -> dict:
    svc = _service(request)
    return {
        "status": "ok",
        "version": __version__,
        "demo_mode": svc.demo_mode,
        "model": svc.settings.gemini_model if not svc.demo_mode else None,
    }


@router.post("/plan", response_model=PlanResponse)
async def create_plan(profile: UserProfile, request: Request) -> PlanResponse:
    svc = _service(request)
    metrics = compute_metrics(profile)
    try:
        plan, model_used = await svc.generate_plan(profile, metrics)
    except GeminiUnavailableError as exc:
        raise HTTPException(
            status_code=502,
            detail="The AI service is temporarily unavailable. Please try again shortly.",
        ) from exc
    return PlanResponse(
        metrics=metrics, plan=plan, model_used=model_used, demo_mode=svc.demo_mode
    )
