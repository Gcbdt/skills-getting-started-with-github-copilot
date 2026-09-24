import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_index():
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_details():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert expected_activity in response.json()
    assert response.json()[expected_activity]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


def test_duplicate_signup_returns_bad_request():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    initial_count = activities[activity_name]["participants"].count(email)

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Student is already signed up for this activity"
    )
    assert activities[activity_name]["participants"].count(email) == initial_count


def test_signup_for_unknown_activity_returns_not_found():
    # Arrange
    activity_name = "Unknown Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_without_email_returns_validation_error():
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup"
    )

    # Assert
    assert response.status_code == 422


def test_unregister_removes_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    encoded_activity = quote(activity_name, safe="")
    encoded_email = quote(email, safe="")

    # Act
    response = client.delete(
        f"/activities/{encoded_activity}/signup/{encoded_email}"
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in activities[activity_name]["participants"]


def test_unregister_from_unknown_activity_returns_not_found():
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/signup/{quote(email, safe='')}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregistering_nonparticipant_returns_not_found():
    # Arrange
    activity_name = "Chess Club"
    email = "not.registered@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/signup/{quote(email, safe='')}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Student is not signed up for this activity"
    )


def test_encoded_activity_and_email_are_supported():
    # Arrange
    activity_name = "Chess Club"
    email = "encoded.student+club@mergington.edu"
    encoded_activity = quote(activity_name, safe="")
    encoded_email = quote(email, safe="")

    # Act
    signup_response = client.post(
        f"/activities/{encoded_activity}/signup",
        params={"email": email},
    )
    delete_response = client.delete(
        f"/activities/{encoded_activity}/signup/{encoded_email}"
    )

    # Assert
    assert signup_response.status_code == 200
    assert delete_response.status_code == 200
    assert email not in activities[activity_name]["participants"]
