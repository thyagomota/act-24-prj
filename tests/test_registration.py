from app.models import Student


def registration_data(**overrides):
    data = {
        "student_id": "S123",
        "full_name": "Taylor Student",
        "email": "taylor@example.edu",
        "password": "securepass",
    }
    data.update(overrides)
    return data


def test_registration_creates_account_and_student_can_log_in(client, app):
    response = client.post("/register", data=registration_data())

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    with app.app_context():
        student = Student.query.one()
        assert student.full_name == "Taylor Student"
        assert student.email == "taylor@example.edu"

    response = client.post(
        "/login", data={"student_id": "S123", "password": "securepass"}
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    response = client.get("/")
    assert b"Welcome, Taylor Student" in response.data


def test_registration_rejects_missing_or_invalid_fields(client, app):
    invalid_requests = [
        (registration_data(student_id=""), b"All fields are required."),
        (registration_data(full_name=""), b"All fields are required."),
        (registration_data(email=""), b"All fields are required."),
        (registration_data(password=""), b"All fields are required."),
        (registration_data(email="not-an-email"), b"valid email address"),
        (registration_data(password="short"), b"at least 8 characters"),
    ]

    for data, expected_message in invalid_requests:
        response = client.post("/register", data=data)
        assert response.status_code == 200
        assert expected_message in response.data
        with app.app_context():
            assert Student.query.count() == 0


def test_registration_rejects_duplicate_student_id_or_email(client, app):
    client.post("/register", data=registration_data())
    with app.app_context():
        original_count = Student.query.count()

    duplicate_requests = [
        registration_data(email="different@example.edu"),
        registration_data(student_id="S456"),
    ]
    for data in duplicate_requests:
        response = client.post("/register", data=data)
        assert response.status_code == 200
        assert b"already exists" in response.data
        with app.app_context():
            assert Student.query.count() == original_count


def test_registration_stores_only_password_hash(client, app):
    client.post("/register", data=registration_data())
    with app.app_context():
        student = Student.query.one()
        assert student.password_hash != "securepass"
        assert student.check_password("securepass")
        assert not hasattr(student, "password")
