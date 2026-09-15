"""Backend API tests for MarsSolPlanner."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://02fd2f56-bda2-4aa6-a1ae-753e8269d95d.preview.emergentagent.com").rstrip("/")


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    return s


# --- Health endpoint ---
def test_health(client):
    r = client.get(f"{BASE_URL}/api/health", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True


# --- Plan endpoint ---
def test_plan_structure(client):
    r = client.get(f"{BASE_URL}/api/plan", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert "winner" in data
    assert "timeline" in data
    assert "ranked_deposits" in data
    assert isinstance(data["timeline"], list)


# --- HTML scene endpoint ---
def test_scene_html(client):
    r = client.get(f"{BASE_URL}/api/mars/plan_three.html", timeout=30)
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "").lower()
    html = r.text
    assert "__PAYLOAD__" not in html, "unreplaced placeholder found"
    assert "three" in html.lower() or "THREE" in html
    assert len(html) > 5000


# --- 404 for unknown mars file ---
def test_mars_notfound(client):
    r = client.get(f"{BASE_URL}/api/mars/nonexistent_xyz.html", timeout=15)
    assert r.status_code == 404


# --- Regenerate pipeline (slow ~30-60s) ---
def test_regenerate(client):
    r = client.post(f"{BASE_URL}/api/regenerate", timeout=120)
    assert r.status_code == 200, r.text[:500]
    data = r.json()
    assert data.get("ok") is True
