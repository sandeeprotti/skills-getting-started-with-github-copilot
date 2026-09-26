from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_participants = {
        name: list(activity["participants"])
        for name, activity in activities.items()
    }

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        for name, participants in original_participants.items():
            activities[name]["participants"][:] = participants


def test_get_activities_returns_activity_data(client):
    # Arrange
    activity_name = "Soccer Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()[activity_name]["participants"] == []


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Soccer Club"
    email = "new.student@mergington.edu"
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert activities[activity_name]["participants"].count(email) == 1


def test_duplicate_signup_returns_bad_request(client):
    # Arrange
    activity_name = "Soccer Club"
    email = "existing.student@mergington.edu"
    activities[activity_name]["participants"].append(email)
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activities[activity_name]["participants"].count(email) == 1


def test_signup_for_unknown_activity_returns_not_found(client):
    # Arrange
    activity_name = "Unknown Club"
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(signup_url, params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    # Arrange
    activity_name = "Soccer Club"
    email = "registered.student@mergington.edu"
    activities[activity_name]["participants"].append(email)
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.delete(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_unregister_for_absent_participant_returns_not_found(client):
    # Arrange
    activity_name = "Soccer Club"
    email = "absent.student@mergington.edu"
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.delete(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_from_unknown_activity_returns_not_found(client):
    # Arrange
    activity_name = "Unknown Club"
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.delete(signup_url, params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"