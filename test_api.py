import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

PROFILE = {
    "name": "Alex", "age": 28, "gender": "male", "height_cm": 175, "weight_kg": 72,
    "goal": "muscle_gain", "activity_level": "moderate", "experience": "intermediate",
    "days_per_week": 4, "session_minutes": 45, "equipment": "gym",
    "diet": "vegetarian", "limitations": "",
}


@pytest.fixture()
def client():
    app = create_app(Settings(gemini_api_key="", rate_limit_per_minute=1000))
    with TestClient(app) as c:
        yield c


def test_index_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Build your plan" in r.text


def test_static_css(client):
    assert client.get("/static/css/style.css").status_code == 200


def test_health_reports_demo_mode(client):
    data = client.get("/api/health").json()
    assert data["status"] == "ok" and data["demo_mode"] is True


def test_form_submission_renders_plan(client):
    r = client.post("/generate", data={k: str(v) for k, v in PROFILE.items()})
    assert r.status_code == 200
    assert "Your weekly plan" in r.text
    assert r.text.count('class="card day"') == 4


def test_form_validation_keeps_values(client):
    r = client.post("/generate", data={**{k: str(v) for k, v in PROFILE.items()}, "age": "5", "name": "Sam"})
    assert r.status_code == 422
    assert "Age" in r.text and 'value="Sam"' in r.text


def test_form_output_is_escaped(client):
    r = client.post("/generate", data={**{k: str(v) for k, v in PROFILE.items()}, "name": "<script>x</script>"})
    assert "<script>x</script>" not in r.text


@pytest.mark.parametrize("days", [1, 3, 5, 7])
def test_api_plan_has_requested_days(client, days):
    r = client.post("/api/plan", json={**PROFILE, "days_per_week": days})
    assert r.status_code == 200
    body = r.json()
    assert len(body["plan"]["weekly_schedule"]) == days
    assert body["plan"]["nutrition"]["daily_calories"] == body["metrics"]["target_calories"]


@pytest.mark.parametrize("equipment", ["none", "home_basic", "gym"])
@pytest.mark.parametrize("goal", ["weight_loss", "muscle_gain", "general_wellness", "endurance", "strength"])
def test_api_all_goal_equipment_combos(client, goal, equipment):
    assert client.post("/api/plan", json={**PROFILE, "goal": goal, "equipment": equipment}).status_code == 200


def test_api_validation_error_is_friendly(client):
    r = client.post("/api/plan", json={**PROFILE, "age": 5})
    assert r.status_code == 422 and "age" in r.json()["detail"]


def test_rate_limit():
    app = create_app(Settings(gemini_api_key="", rate_limit_per_minute=2))
    with TestClient(app) as c:
        codes = [c.post("/api/plan", json=PROFILE).status_code for _ in range(3)]
    assert codes == [200, 200, 429]
