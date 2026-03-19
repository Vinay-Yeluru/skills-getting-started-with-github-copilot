"""
Tests for Mergington High School Activity Management API

Uses FastAPI TestClient with AAA (Arrange-Act-Assert) pattern to test:
- GET /activities endpoint
- POST /activities/{activity_name}/signup endpoint
- DELETE /activities/{activity_name}/participants endpoint
"""

import pytest
import copy
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


class TestGetActivities:
    def test_get_activities_returns_all_activities(self):
        # Arrange
        client = TestClient(app)

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert all(isinstance(a.get("participants"), list) for a in data.values())


class TestSignupForActivity:
    def test_signup_success(self):
        # Arrange
        client = TestClient(app)
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        original_count = len(activities[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == original_count + 1

    def test_signup_duplicate_email(self):
        # Arrange
        client = TestClient(app)
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        original_count = len(activities[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
        assert len(activities[activity_name]["participants"]) == original_count
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_activity_not_found(self):
        # Arrange
        client = TestClient(app)
        nonexistent = "Nonexistent Guild"

        # Act
        response = client.post(
            f"/activities/{nonexistent}/signup",
            params={"email": "test@mergington.edu"},
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestRemoveParticipant:
    def test_remove_participant_success(self):
        # Arrange
        client = TestClient(app)
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        original_participants = activities[activity_name]["participants"].copy()

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == len(original_participants) - 1
        for participant in [p for p in original_participants if p != email]:
            assert participant in activities[activity_name]["participants"]

    def test_remove_participant_not_registered(self):
        # Arrange
        client = TestClient(app)
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"
        original_participants = activities[activity_name]["participants"].copy()

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert "not registered" in response.json()["detail"].lower()
        assert activities[activity_name]["participants"] == original_participants

    def test_remove_participant_missing_activity(self):
        # Arrange
        client = TestClient(app)
        nonexistent = "Missing Activity"
        activities_state = copy.deepcopy(activities)

        # Act
        response = client.delete(
            f"/activities/{nonexistent}/participants",
            params={"email": "test@mergington.edu"},
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        assert activities == activities_state
