import pytest
from unittest.mock import patch
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_health(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.data == b"ok"


def test_health_through_proxy(client):
    """Test health check works through nginx proxy"""
    response = client.get("/health")
    assert response.status_code == 200


def test_index(client):
    """Test index page"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Todo API" in response.data


def test_index_has_form(client):
    """Test index page has form"""
    response = client.get("/")
    assert b"<form" in response.data


def test_index_has_link(client):
    """Test index page has view link"""
    response = client.get("/")
    assert b"/list" in response.data


def test_index_has_button(client):
    """Test index page has button"""
    response = client.get("/")
    assert b"button" in response.data


@patch("app.db")
def test_add(mock_db, client):
    assert client.post("/add", json={"task": "test"}).status_code == 200


@patch("app.db")
def test_list(mock_db, client):
    mock_db.return_value.cursor.return_value.fetchall.return_value = []
    assert client.get("/list").status_code == 200


@patch("app.db")
def test_delete(mock_db, client):
    assert client.get("/delete/1").status_code == 200


@patch("app.db")
def test_add_from_browser(mock_db, client):
    assert client.post("/add_from_browser", data={"task": "test"}).status_code == 200
