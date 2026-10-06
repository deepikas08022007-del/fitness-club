from app.schemas import UserProfile
from app.utils.health import bmi_category, calc_bmi, compute_metrics


def make_profile(**kw):
    base = dict(age=30, gender="male", height_cm=180, weight_kg=80, goal="general_wellness")
    base.update(kw)
    return UserProfile(**base)


def test_bmi_and_category():
    assert calc_bmi(80, 180) == 24.7
    assert bmi_category(24.7) == "Healthy weight"
    assert bmi_category(17) == "Underweight"
    assert bmi_category(27) == "Overweight"
    assert bmi_category(32) == "Obese"


def test_weight_loss_is_deficit_and_muscle_gain_is_surplus():
    maintain = compute_metrics(make_profile())
    loss = compute_metrics(make_profile(goal="weight_loss"))
    gain = compute_metrics(make_profile(goal="muscle_gain"))
    assert loss.target_calories < maintain.target_calories < gain.target_calories


def test_calorie_floor():
    m = compute_metrics(make_profile(gender="female", weight_kg=45, height_cm=150, age=60,
                                     activity_level="sedentary", goal="weight_loss"))
    assert m.target_calories >= 1200
