"""Server-rendered HTML pages (no JavaScript required)."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app import __version__
from app.schemas import UserProfile
from app.services.gemini_service import GeminiUnavailableError
from app.utils.health import compute_metrics

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(include_in_schema=False)

DEFAULT_VALUES = {
    "name": "", "age": "", "gender": "male", "height_cm": "", "weight_kg": "",
    "goal": "general_wellness", "activity_level": "light", "experience": "beginner",
    "days_per_week": "4", "session_minutes": "45", "equipment": "home_basic",
    "diet": "no_preference", "limitations": "",
}

FIELD_LABELS = {
    "age": "Age", "height_cm": "Height", "weight_kg": "Weight", "name": "Name",
    "limitations": "Injuries / allergies",
}


def _base_context(request: Request) -> dict:
    return {
        "app_name": request.app.state.settings.app_name,
        "version": __version__,
        "demo_mode": request.app.state.gemini.demo_mode,
    }


def _render_form(request: Request, values: dict, error: str | None = None, status: int = 200):
    return templates.TemplateResponse(
        request,
        "index.html",
        {**_base_context(request), "v": values, "error": error},
        status_code=status,
    )


def _friendly_errors(exc: ValidationError) -> str:
    problems = []
    for err in exc.errors():
        field = str(err["loc"][0]) if err["loc"] else "input"
        label = FIELD_LABELS.get(field, field.replace("_", " ").capitalize())
        problems.append(f"{label}: {err['msg']}")
    return "Please check your inputs. " + "; ".join(problems)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return _render_form(request, DEFAULT_VALUES)


@router.post("/generate", response_class=HTMLResponse)
async def generate(request: Request):
    form = await request.form()
    values = {**DEFAULT_VALUES, **{k: str(v).strip() for k, v in form.items() if k in DEFAULT_VALUES}}

    try:
        profile = UserProfile.model_validate(values)
    except ValidationError as exc:
        return _render_form(request, values, _friendly_errors(exc), status=422)

    metrics = compute_metrics(profile)
    try:
        plan, model_used = await request.app.state.gemini.generate_plan(profile, metrics)
    except GeminiUnavailableError:
        return _render_form(
            request,
            values,
            "The AI service is temporarily unavailable. Please try again in a moment.",
            status=502,
        )

    return templates.TemplateResponse(
        request,
        "result.html",
        {
            **_base_context(request),
            "profile": profile,
            "metrics": metrics,
            "plan": plan,
            "model_used": model_used,
            "macro_pct": _macro_percentages(plan.nutrition),
        },
    )


def _macro_percentages(n) -> dict:
    p, c, f = n.protein_g * 4, n.carbs_g * 4, n.fat_g * 9
    total = (p + c + f) or 1
    return {"protein": round(p / total * 100, 1), "carbs": round(c / total * 100, 1), "fat": round(f / total * 100, 1)}
