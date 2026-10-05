"""Deterministic health calculations (BMI, BMR, TDEE, calorie and macro targets).

These numbers are computed server-side so the AI-generated plan stays
consistent with them, instead of letting the model guess.
"""

from app.schemas import HealthMetrics, UserProfile

ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

PROTEIN_G_PER_KG = {
    "weight_loss": 2.0,
    "muscle_gain": 1.8,
    "strength": 1.8,
    "endurance": 1.5,
    "general_wellness": 1.4,
}


def calc_bmi(weight_kg: float, height_cm: float) -> float:
    meters = height_cm / 100
    return round(weight_kg / (meters * meters), 1)


def bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Healthy weight"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def calc_bmr(gender: str, weight_kg: float, height_cm: float, age: int) -> float:
    """Mifflin-St Jeor equation."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    offset = {"male": 5, "female": -161}.get(gender, -78)
    return base + offset


def calc_target_calories(tdee: float, bmr: float, goal: str) -> int:
    if goal == "weight_loss":
        target = tdee * 0.80
        floor = max(bmr, 1200)
        return int(round(max(target, floor)))
    if goal == "muscle_gain":
        return int(round(tdee * 1.10))
    return int(round(tdee))


def calc_macros(calories: int, weight_kg: float, goal: str) -> tuple[int, int, int]:
    protein = round(weight_kg * PROTEIN_G_PER_KG.get(goal, 1.4))
    fat = round(calories * 0.25 / 9)
    carbs = round(max(calories - protein * 4 - fat * 9, 0) / 4)
    return protein, carbs, fat


def compute_metrics(profile: UserProfile) -> HealthMetrics:
    bmi = calc_bmi(profile.weight_kg, profile.height_cm)
    bmr = calc_bmr(profile.gender, profile.weight_kg, profile.height_cm, profile.age)
    tdee = bmr * ACTIVITY_FACTORS[profile.activity_level]
    target = calc_target_calories(tdee, bmr, profile.goal)
    protein, carbs, fat = calc_macros(target, profile.weight_kg, profile.goal)
    return HealthMetrics(
        bmi=bmi,
        bmi_category=bmi_category(bmi),
        bmr=int(round(bmr)),
        tdee=int(round(tdee)),
        target_calories=target,
        protein_g=protein,
        carbs_g=carbs,
        fat_g=fat,
    )
