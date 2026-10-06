"""Prompt templates for the Gemini models."""

from app.schemas import HealthMetrics, UserProfile

PLAN_SYSTEM_INSTRUCTION = """\
You are FitBuddy, an experienced certified personal trainer and sports nutritionist.
You create safe, realistic, personalised workout and nutrition plans.

Rules:
- Return ONLY JSON matching the provided schema. No markdown, no commentary.
- Create exactly the requested number of training days in weekly_schedule.
- Respect the user's equipment, experience level, session length, diet and limitations.
- Use the supplied calorie and macro targets in the nutrition section.
- Keep exercise names standard and recognisable. Give short, practical form cues.
- Include 4 sample meals (Breakfast, Lunch, Dinner, Snack) that fit the diet.
- Never give medical diagnoses. Add sensible safety notes, and advise consulting a
  doctor for injuries, medical conditions, pregnancy, or if the user is under 18.
"""

def build_plan_prompt(profile: UserProfile, metrics: HealthMetrics) -> str:
    goal = profile.goal.replace("_", " ")
    return f"""\
Create a personalised weekly fitness plan for this person.

PROFILE
- Name: {profile.name or "Not provided"}
- Age: {profile.age}
- Gender: {profile.gender}
- Height: {profile.height_cm} cm
- Weight: {profile.weight_kg} kg
- Goal: {goal}
- Current activity level: {profile.activity_level.replace("_", " ")}
- Training experience: {profile.experience}
- Training days per week: {profile.days_per_week}
- Time per session: {profile.session_minutes} minutes
- Equipment: {profile.equipment.replace("_", " ")}
- Diet preference: {profile.diet.replace("_", " ")}
- Injuries / limitations / allergies: {profile.limitations or "None"}

COMPUTED TARGETS (use these exact numbers in the nutrition section)
- BMI: {metrics.bmi} ({metrics.bmi_category})
- Daily calories: {metrics.target_calories} kcal
- Protein: {metrics.protein_g} g, Carbs: {metrics.carbs_g} g, Fat: {metrics.fat_g} g

REQUIREMENTS
- weekly_schedule must contain exactly {profile.days_per_week} workout days labelled "Day 1", "Day 2", ...
- Each workout should fit within about {profile.session_minutes} minutes.
- summary: 2-3 motivating sentences addressed to the user.
- Include warm-up and cool-down items, hydration target, recovery tips,
  progression tips (how to progress week over week) and safety notes.
"""
