"""
test_setup.py - Basic tests to ensure the testing environment is configured correctly.
"""

def test_app_creation(app):
    """
    Test if the Flask app fixture is created successfully.
    """
    assert app is not None
    assert app.config["TESTING"] is True

def test_home_page_unauthenticated(client):
    """
    Test that the home page loads and shows the login button for an unauthenticated user.
    """
    response = client.get('/')
    assert response.status_code == 200
    assert b"Login with Spotify" in response.data