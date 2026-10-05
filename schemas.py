"""Pydantic models for requests, responses and the Gemini structured output."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

Goal = Literal["weight_loss", "muscle_gain", "general_wellness", "endurance", "strength"]
Gender = Literal["male", "female", "other"]
ActivityLevel = Literal["sedentary", "light", "moderate", "active", "very_active"]
Experience = Literal["beginner", "intermediate", "advanced"]
Equipment = Literal["none", "home_basic", "gym"]
Diet = Literal["no_preference", "vegetarian", "vegan", "eggetarian", "pescatarian"]


class UserProfile(BaseModel):
    """What the user submits from the form."""

    name: str = Field(default="", max_length=60)
    age: int = Field(ge=14, le=90)
    gender: Gender
    height_cm: float = Field(ge=100, le=250)
    weight_kg: float = Field(ge=30, le=300)
    goal: Goal
    activity_level: ActivityLevel = "light"
    experience: Experience = "beginner"
    days_per_week: int = Field(default=4, ge=1, le=7)
    session_minutes: int = Field(default=45, ge=15, le=120)
    equipment: Equipment = "home_basic"
    diet: Diet = "no_preference"
    limitations: str = Field(
        default="", max_length=300, description="Injuries, conditions or allergies"
    )


class HealthMetrics(BaseModel):
    bmi: float
    bmi_category: str
    bmr: int
    tdee: int
    target_calories: int
    protein_g: int
    carbs_g: int
    fat_g: int


# ---- Structured plan (also used as Gemini response_schema) -----------------


class Exercise(BaseModel):
    name: str
    sets: int
    reps: str = Field(description="Rep range or duration, e.g. '8-12' or '30 sec'")
    rest_seconds: int
    notes: str = Field(description="Short form cue or progression tip")


class WorkoutDay(BaseModel):
    day_label: str = Field(description="e.g. 'Day 1'")
    focus: str = Field(description="e.g. 'Upper body push'")
    duration_minutes: int
    warmup: list[str]
    exercises: list[Exercise]
    cooldown: list[str]


class Meal(BaseModel):
    meal: str = Field(description="Breakfast, Lunch, Dinner or Snack")
    idea: str
    approx_calories: int


class NutritionPlan(BaseModel):
    daily_calories: int
    protein_g: int
    carbs_g: int
    fat_g: int
    hydration_liters: float
    tips: list[str]
    sample_meals: list[Meal]


class FitnessPlan(BaseModel):
    summary: str
    weekly_schedule: list[WorkoutDay]
    nutrition: NutritionPlan
    recovery_tips: list[str]
    progress_tips: list[str]
    safety_notes: list[str]


class PlanResponse(BaseModel):
    metrics: HealthMetrics
    plan: FitnessPlan
    model_used: str
    demo_mode: bool
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
