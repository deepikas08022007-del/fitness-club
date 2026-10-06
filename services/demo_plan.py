"""Rule-based fallback plan generator.

Used when no Gemini API key is configured (demo mode) so the application still
works end to end. The structure is identical to the Gemini output.
"""

from app.schemas import (
    Exercise,
    FitnessPlan,
    HealthMetrics,
    Meal,
    NutritionPlan,
    UserProfile,
    WorkoutDay,
)

EXERCISES: dict[str, dict[str, list[tuple[str, str]]]] = {
    "none": {
        "push": [("Push-ups", "Keep your body in a straight line"), ("Pike Push-ups", "Hips high, head between arms"), ("Bench Dips (chair)", "Elbows point back, not out")],
        "pull": [("Superman Hold", "Squeeze glutes and upper back"), ("Reverse Snow Angels", "Move slowly, lead with the thumbs"), ("Towel Row (door)", "Pull elbows to ribs")],
        "legs": [("Bodyweight Squats", "Chest up, knees track over toes"), ("Reverse Lunges", "Step back, keep torso tall"), ("Glute Bridges", "Pause and squeeze at the top")],
        "core": [("Plank", "Brace your abs, do not sag"), ("Dead Bug", "Lower back stays flat"), ("Bicycle Crunch", "Slow and controlled")],
        "cardio": [("Jumping Jacks", "Land softly"), ("High Knees", "Drive knees to hip height"), ("Mountain Climbers", "Keep hips low")],
    },
    "home_basic": {
        "push": [("Dumbbell Floor Press", "Elbows at 45 degrees"), ("Push-ups", "Full range of motion"), ("Dumbbell Shoulder Press", "Do not arch your back")],
        "pull": [("One-arm Dumbbell Row", "Pull elbow to hip"), ("Resistance Band Pull-apart", "Squeeze shoulder blades"), ("Dumbbell Reverse Fly", "Light weight, slow tempo")],
        "legs": [("Goblet Squat", "Sit between your hips"), ("Dumbbell Romanian Deadlift", "Hinge at the hips, flat back"), ("Dumbbell Walking Lunges", "Long stride, upright torso")],
        "core": [("Plank", "Brace your abs"), ("Russian Twist", "Rotate through the ribs"), ("Hanging Knee Raise / Leg Raise", "Avoid swinging")],
        "cardio": [("Jump Rope", "Stay light on your toes"), ("Dumbbell Thrusters", "Use legs to drive the press"), ("Burpees", "Maintain steady form")],
    },
    "gym": {
        "push": [("Barbell Bench Press", "Retract shoulder blades, feet planted"), ("Incline Dumbbell Press", "Control the descent"), ("Cable Triceps Pushdown", "Elbows pinned to sides")],
        "pull": [("Lat Pulldown", "Pull to upper chest"), ("Seated Cable Row", "Chest tall, squeeze at the end"), ("Face Pull", "Pull toward your forehead")],
        "legs": [("Barbell Back Squat", "Brace, hit depth you control"), ("Leg Press", "Do not lock out the knees"), ("Romanian Deadlift", "Hinge, keep the bar close")],
        "core": [("Cable Crunch", "Curl the ribs to the hips"), ("Hanging Leg Raise", "No swinging"), ("Plank", "Stay braced")],
        "cardio": [("Treadmill Intervals", "30 sec fast, 60 sec easy"), ("Rowing Machine", "Legs, then back, then arms"), ("Stationary Bike", "Maintain steady cadence")],
    },
}

SPLITS: dict[int, list[str]] = {
    1: ["full"],
    2: ["full", "full"],
    3: ["full", "full", "full"],
    4: ["upper", "lower", "upper", "lower"],
    5: ["push", "pull", "legs", "upper", "cardio"],
    6: ["push", "pull", "legs", "push", "pull", "legs"],
    7: ["push", "pull", "legs", "upper", "lower", "cardio", "mobility"],
}

SPLIT_GROUPS = {
    "full": ["push", "pull", "legs", "core"],
    "upper": ["push", "pull", "core"],
    "lower": ["legs", "core"],
    "push": ["push", "core"],
    "pull": ["pull", "core"],
    "legs": ["legs", "core"],
    "cardio": ["cardio", "core"],
}

FOCUS_LABEL = {
    "full": "Full body",
    "upper": "Upper body",
    "lower": "Lower body & core",
    "push": "Push (chest, shoulders, triceps)",
    "pull": "Pull (back, biceps)",
    "legs": "Legs & core",
    "cardio": "Conditioning & core",
    "mobility": "Active recovery & mobility",
}

MEALS = {
    "no_preference": [
        ("Breakfast", "Greek yogurt bowl with oats, berries and nuts", 0.25),
        ("Lunch", "Grilled chicken, brown rice and mixed vegetables", 0.30),
        ("Dinner", "Baked fish or lean meat with sweet potato and salad", 0.30),
        ("Snack", "Banana with peanut butter or a protein shake", 0.15),
    ],
    "vegetarian": [
        ("Breakfast", "Vegetable besan chilla with curd", 0.25),
        ("Lunch", "Paneer, quinoa and sautéed vegetables", 0.30),
        ("Dinner", "Dal, roti and a large salad", 0.30),
        ("Snack", "Roasted chickpeas and fruit", 0.15),
    ],
    "vegan": [
        ("Breakfast", "Overnight oats with soy milk, chia and fruit", 0.25),
        ("Lunch", "Tofu stir-fry with rice and vegetables", 0.30),
        ("Dinner", "Lentil and vegetable curry with millet roti", 0.30),
        ("Snack", "Hummus with carrots and a handful of almonds", 0.15),
    ],
    "eggetarian": [
        ("Breakfast", "Vegetable omelette with whole-grain toast", 0.25),
        ("Lunch", "Egg curry, brown rice and salad", 0.30),
        ("Dinner", "Paneer or tofu with roti and vegetables", 0.30),
        ("Snack", "Boiled eggs and fruit", 0.15),
    ],
    "pescatarian": [
        ("Breakfast", "Scrambled eggs with spinach and whole-grain toast", 0.25),
        ("Lunch", "Tuna or salmon bowl with rice and greens", 0.30),
        ("Dinner", "Grilled fish with quinoa and roasted vegetables", 0.30),
        ("Snack", "Greek yogurt with nuts", 0.15),
    ],
}

GOAL_SUMMARY = {
    "weight_loss": "a moderate calorie deficit with strength training and conditioning to lose fat while keeping muscle",
    "muscle_gain": "progressive overload and a small calorie surplus to build lean muscle",
    "general_wellness": "balanced strength, movement and nutrition habits for long-term health",
    "endurance": "conditioning work plus supporting strength to improve stamina",
    "strength": "heavy, low-rep compound lifting to get stronger safely",
}


def _scheme(goal: str, experience: str) -> tuple[int, str, int]:
    if goal == "strength":
        sets, reps, rest = 5, "5", 120
    elif goal == "muscle_gain":
        sets, reps, rest = 4, "8-12", 75
    elif goal == "weight_loss":
        sets, reps, rest = 3, "12-15", 45
    elif goal == "endurance":
        sets, reps, rest = 3, "15-20", 40
    else:
        sets, reps, rest = 3, "10-12", 60
    if experience == "beginner":
        sets = max(2, sets - 1)
    return sets, reps, rest


def build_demo_plan(profile: UserProfile, metrics: HealthMetrics) -> FitnessPlan:
    sets, reps, rest = _scheme(profile.goal, profile.experience)
    per_group = 2 if profile.experience == "beginner" or profile.session_minutes <= 30 else 3
    bank = EXERCISES[profile.equipment]
    split = SPLITS[profile.days_per_week]

    schedule: list[WorkoutDay] = []
    for i, kind in enumerate(split, start=1):
        label = f"Day {i}"
        if kind == "mobility":
            schedule.append(
                WorkoutDay(
                    day_label=label,
                    focus=FOCUS_LABEL[kind],
                    duration_minutes=min(profile.session_minutes, 30),
                    warmup=["5 min easy walk"],
                    exercises=[
                        Exercise(name="Cat-Cow", sets=2, reps="10", rest_seconds=20, notes="Move with your breath"),
                        Exercise(name="World's Greatest Stretch", sets=2, reps="5 per side", rest_seconds=20, notes="Open the chest and hips"),
                        Exercise(name="Foam Roll / Self-massage", sets=1, reps="5 min", rest_seconds=0, notes="Avoid rolling directly on joints"),
                    ],
                    cooldown=["Slow nasal breathing for 2 minutes"],
                )
            )
            continue

        exercises: list[Exercise] = []
        for group in SPLIT_GROUPS[kind]:
            for name, note in bank[group][:per_group]:
                is_cardio = group == "cardio"
                exercises.append(
                    Exercise(
                        name=name,
                        sets=3 if is_cardio else sets,
                        reps="40 sec" if is_cardio else (reps if group != "core" else "30-45 sec" if "Plank" in name else "12-15"),
                        rest_seconds=30 if is_cardio else rest,
                        notes=note,
                    )
                )
        if profile.goal in ("weight_loss", "endurance") and kind != "cardio":
            name, note = bank["cardio"][0]
            exercises.append(Exercise(name=f"Finisher: {name}", sets=4, reps="30 sec", rest_seconds=30, notes=note))

        schedule.append(
            WorkoutDay(
                day_label=label,
                focus=FOCUS_LABEL[kind],
                duration_minutes=profile.session_minutes,
                warmup=["5 min light cardio", "Dynamic stretches: arm circles, hip circles, leg swings"],
                exercises=exercises,
                cooldown=["3-5 min easy walk", "Static stretch the worked muscles for 30 sec each"],
            )
        )

    meals = [
        Meal(meal=m, idea=idea, approx_calories=int(round(metrics.target_calories * share, -1)))
        for m, idea, share in MEALS[profile.diet if profile.diet in MEALS else "no_preference"]
    ]
    nutrition = NutritionPlan(
        daily_calories=metrics.target_calories,
        protein_g=metrics.protein_g,
        carbs_g=metrics.carbs_g,
        fat_g=metrics.fat_g,
        hydration_liters=round(max(2.0, profile.weight_kg * 0.035), 1),
        tips=[
            f"Aim for about {metrics.protein_g} g of protein spread over 3-4 meals.",
            "Fill half your plate with vegetables and choose mostly whole foods.",
            "Have a carbohydrate and protein meal 1-2 hours before training.",
            "Limit sugary drinks and heavily processed snacks.",
        ],
        sample_meals=meals,
    )

    name = profile.name.strip() or "there"
    return FitnessPlan(
        summary=(
            f"Hi {name}! This {profile.days_per_week}-day plan focuses on {GOAL_SUMMARY[profile.goal]}. "
            f"Your daily target is about {metrics.target_calories} kcal. Stay consistent, "
            "and the results will follow."
        ),
        weekly_schedule=schedule,
        nutrition=nutrition,
        recovery_tips=[
            "Sleep 7-9 hours per night.",
            "Take at least one full rest day per week.",
            "Walk 6,000-10,000 steps daily on non-training days.",
        ],
        progress_tips=[
            "Add 1-2 reps or a small amount of weight when all sets feel easy.",
            "Track your workouts and body weight weekly, not daily.",
            "Every 4-6 weeks, reduce volume for one easier week (deload).",
        ],
        safety_notes=[
            "Stop any exercise that causes sharp or unusual pain.",
            "Consult a doctor before starting if you have medical conditions, injuries or are pregnant"
            + (", and get guardian guidance as you are under 18." if profile.age < 18 else "."),
            "This demo plan is rule-based. Add a Gemini API key for fully AI-personalised plans.",
        ],
    )
