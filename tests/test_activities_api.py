from copy import deepcopy

import pytest


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_catalog(client, initial_activities):
    # Arrange
    expected_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == initial_activities
    assert response.json()
    for activity_name, activity in response.json().items():
        assert isinstance(activity_name, str)
        assert set(activity) == expected_fields
        assert isinstance(activity["description"], str)
        assert isinstance(activity["schedule"], str)
        assert isinstance(activity["max_participants"], int)
        assert isinstance(activity["participants"], list)
        assert all(isinstance(email, str) for email in activity["participants"])


def test_signup_adds_participant(client, initial_activities):
    # Arrange
    activity_name = "Chess Club"
    email = "new+student@mergington.edu"
    expected_activities = deepcopy(initial_activities)
    expected_activities[activity_name]["participants"].append(email)

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert activities_response.status_code == 200
    assert activities_response.json() == expected_activities


def test_duplicate_signup_leaves_activities_unchanged(client, initial_activities):
    # Arrange
    activity_name = "Chess Club"
    email = initial_activities[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert activities_response.status_code == 200
    assert activities_response.json() == initial_activities


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_unknown_activity_leaves_activities_unchanged(
    client, initial_activities, method
):
    # Arrange
    activity_name = "Unknown Club"
    email = "new+student@mergington.edu"

    # Act
    response = client.request(
        method, f"/activities/{activity_name}/signup", params={"email": email}
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activities_response.status_code == 200
    assert activities_response.json() == initial_activities


def test_unregister_removes_participant(client, initial_activities):
    # Arrange
    activity_name = "Chess Club"
    email = initial_activities[activity_name]["participants"][0]
    expected_activities = deepcopy(initial_activities)
    expected_activities[activity_name]["participants"].remove(email)

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup", params={"email": email}
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert activities_response.status_code == 200
    assert activities_response.json() == expected_activities


def test_unregister_unknown_participant_leaves_activities_unchanged(
    client, initial_activities
):
    # Arrange
    activity_name = "Chess Club"
    email = "new+student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup", params={"email": email}
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert activities_response.status_code == 200
    assert activities_response.json() == initial_activities


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_missing_email_leaves_activities_unchanged(client, initial_activities, method):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.request(method, f"/activities/{activity_name}/signup")
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 422
    assert any(
        error["loc"] == ["query", "email"] for error in response.json()["detail"]
    )
    assert activities_response.status_code == 200
    assert activities_response.json() == initial_activities


def test_signup_then_unregister_restores_initial_state(client, initial_activities):
    # Arrange
    activity_name = "Chess Club"
    email = "new+student@mergington.edu"
    signup_url = f"/activities/{activity_name}/signup"
    expected_signed_up_activities = deepcopy(initial_activities)
    expected_signed_up_activities[activity_name]["participants"].append(email)

    # Act
    signup_response = client.post(signup_url, params={"email": email})
    signed_up_activities_response = client.get("/activities")
    unregister_response = client.delete(signup_url, params={"email": email})
    final_activities_response = client.get("/activities")

    # Assert
    assert signup_response.status_code == 200
    assert signup_response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert signed_up_activities_response.status_code == 200
    assert signed_up_activities_response.json() == expected_signed_up_activities
    assert unregister_response.status_code == 200
    assert unregister_response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert final_activities_response.status_code == 200
    assert final_activities_response.json() == initial_activities