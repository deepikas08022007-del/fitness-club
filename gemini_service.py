"""Gemini integration with structured output, model fallback and a demo mode."""

import logging

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.config import Settings
from app.schemas import FitnessPlan, HealthMetrics, UserProfile
from app.services.demo_plan import build_demo_plan
from app.services.prompts import PLAN_SYSTEM_INSTRUCTION, build_plan_prompt

logger = logging.getLogger("fitbuddy.gemini")


class GeminiUnavailableError(Exception):
    """Raised when every configured Gemini model failed."""


class GeminiService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.demo_mode = not settings.has_api_key
        self._client: genai.Client | None = None
        if not self.demo_mode:
            self._client = genai.Client(
                api_key=settings.gemini_api_key.strip(),
                http_options=types.HttpOptions(
                    timeout=settings.gemini_timeout_seconds * 1000
                ),
            )

    @property
    def models(self) -> list[str]:
        ordered = [self.settings.gemini_model, self.settings.gemini_fallback_model]
        return [m for i, m in enumerate(ordered) if m and m not in ordered[:i]]

    # ------------------------------------------------------------------ plan
    async def generate_plan(
        self, profile: UserProfile, metrics: HealthMetrics
    ) -> tuple[FitnessPlan, str]:
        """Return (plan, model_name)."""
        if self.demo_mode:
            return build_demo_plan(profile, metrics), "demo-rule-engine"

        prompt = build_plan_prompt(profile, metrics)
        last_error: Exception | None = None
        for model in self.models:
            try:
                response = await self._client.aio.models.generate_content(  # type: ignore[union-attr]
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=PLAN_SYSTEM_INSTRUCTION,
                        temperature=self.settings.gemini_temperature,
                        response_mime_type="application/json",
                        response_schema=FitnessPlan,
                    ),
                )
                plan = self._parse_plan(response)
                plan = self._normalise(plan, profile)
                return plan, model
            except Exception as exc:  # noqa: BLE001 - try the next model
                last_error = exc
                logger.warning("Gemini model %s failed: %s", model, exc)
                if isinstance(exc, genai_errors.ClientError) and getattr(exc, "code", None) in (400, 401, 403):
                    # Bad key / bad request will not be fixed by another model.
                    break
        raise GeminiUnavailableError(str(last_error))

    @staticmethod
    def _parse_plan(response) -> FitnessPlan:
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, FitnessPlan):
            return parsed
        text = (response.text or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            text = text.removeprefix("json").strip()
        return FitnessPlan.model_validate_json(text)

    @staticmethod
    def _normalise(plan: FitnessPlan, profile: UserProfile) -> FitnessPlan:
        if not plan.weekly_schedule:
            raise ValueError("Model returned an empty schedule")
        # Guarantee the requested number of days and consistent labels.
        plan.weekly_schedule = plan.weekly_schedule[: profile.days_per_week]
        for i, day in enumerate(plan.weekly_schedule, start=1):
            day.day_label = f"Day {i}"
        return plan
