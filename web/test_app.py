import pytest
import os
import json
from unittest.mock import patch, MagicMock
from app import app, validate_task
import mysql.connector
from mysql.connector import Error as MySQLError


@pytest.fixture
def client():
    """Create Flask test client"""
    app.config["TESTING"] = True
    return app.test_client()


class TestInputValidation:
    """Test input validation functions"""

    def test_validate_task_valid(self):
        """Test validation passes for valid task"""
        result = validate_task("Buy groceries")
        assert result == "Buy groceries"

    def test_validate_task_with_whitespace(self):
        """Test validation strips whitespace"""
        result = validate_task("  Buy groceries  ")
        assert result == "Buy groceries"

    def test_validate_task_none(self):
        """Test validation fails for None"""
        with pytest.raises(ValueError):
            validate_task(None)

    def test_validate_task_empty(self):
        """Test validation fails for empty string"""
        with pytest.raises(ValueError):
            validate_task("")

    def test_validate_task_whitespace_only(self):
        """Test validation fails for whitespace-only string"""
        with pytest.raises(ValueError):
            validate_task("   ")

    def test_validate_task_too_long(self):
        """Test validation fails for task exceeding max length"""
        long_task = "x" * 300
        with pytest.raises(ValueError):
            validate_task(long_task)

    def test_validate_task_not_string(self):
        """Test validation fails for non-string input"""
        with pytest.raises(ValueError):
            validate_task(123)


class TestHealthEndpoint:
    """Test health check endpoint"""

    @patch("app.get_db_connection")
    def test_health_check_success(self, mock_conn, client):
        """Health check returns 200 when DB is healthy"""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_connection

        response = client.get("/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"

    @patch("app.get_db_connection")
    def test_health_check_failure(self, mock_conn, client):
        """Health check returns 503 when DB connection fails"""
        mock_conn.side_effect = MySQLError("Connection refused")

        response = client.get("/health")
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data["status"] == "unhealthy"


class TestAddEndpoint:
    """Test /add endpoint (JSON API)"""

    @patch("app.get_db")
    def test_add_task_success(self, mock_db, client):
        """Test successful task addition returns 201"""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_cursor.lastrowid = 1
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=None)
        mock_db.return_value = mock_connection

        response = client.post("/add", json={"task": "Buy milk"})

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["task"] == "Buy milk"
        assert data["status"] == "pending"
        assert data["task_id"] == 1
        assert "message" in data

    def test_add_task_no_json(self, client):
        """Test add with no JSON body"""
        response = client.post("/add", data="invalid")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_add_task_missing_field(self, client):
        """Test add with missing task field"""
        response = client.post("/add", json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_add_task_empty_task(self, client):
        """Test add with empty task"""
        response = client.post("/add", json={"task": ""})
        assert response.status_code == 400

    def test_add_task_too_long(self, client):
        """Test add with task exceeding max length"""
        long_task = "x" * 300
        response = client.post("/add", json={"task": long_task})
        assert response.status_code == 400

    @patch("app.get_db")
    def test_add_task_db_error(self, mock_db, client):
        """Test add with database error"""
        mock_db.side_effect = MySQLError("Connection error")

        response = client.post("/add", json={"task": "Buy milk"})
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data["error"] == "Database error"


class TestListEndpoint:
    """Test /list endpoint (HTML view)"""

    @patch("app.get_db")
    def test_list_empty(self, mock_db, client):
        """Test list with no tasks"""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=None)
        mock_db.return_value = mock_connection

        response = client.get("/list")
        assert response.status_code == 200
        assert b"<table" in response.data

    @patch("app.get_db")
    def test_list_with_tasks(self, mock_db, client):
        """Test list with tasks"""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, "Buy milk", "pending"),
            (2, "Read book", "completed"),
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=None)
        mock_db.return_value = mock_connection

        response = client.get("/list")
        assert response.status_code == 200
        assert b"Buy milk" in response.data
        assert b"pending" in response.data


class TestTasksAPIEndpoint:
    """Test /tasks endpoint (JSON API with pagination)"""

    @patch("app.get_db")
    def test_tasks_api_success(self, mock_db, client):
        """Test getting tasks via API"""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"id": 1, "task": "Buy milk", "status": "pending"}
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=None)
        mock_db.return_value = mock_connection

        response = client.get("/tasks")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "tasks" in data
        assert "page" in data

    def test_tasks_api_invalid_page(self, client):
        """Test tasks API with invalid page number"""
        response = client.get("/tasks?page=0")
        assert response.status_code == 400

    def test_tasks_api_invalid_per_page(self, client):
        """Test tasks API with invalid per_page"""
        response = client.get("/tasks?per_page=200")
        assert response.status_code == 400


class TestCompleteEndpoint:
    """Test /complete/<id> endpoint"""

    @patch("app.get_db")
    def test_complete_task_success(self, mock_db, client):
        """Test marking task as complete"""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=None)
        mock_db.return_value = mock_connection

        response = client.post("/complete/1")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "Task marked complete"

    @patch("app.get_db")
    def test_complete_task_not_found(self, mock_db, client):
        """Test completing non-existent task"""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=None)
        mock_db.return_value = mock_connection

        response = client.post("/complete/999")
        assert response.status_code == 404


class TestDeleteEndpoint:
    """Test /delete/<id> endpoint"""

    @patch("app.get_db")
    def test_delete_task_success(self, mock_db, client):
        """Test deleting a task"""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=None)
        mock_db.return_value = mock_connection

        response = client.post("/delete/1")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "Task deleted"

    @patch("app.get_db")
    def test_delete_task_not_found(self, mock_db, client):
        """Test deleting non-existent task"""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = MagicMock(return_value=mock_connection)
        mock_connection.__exit__ = MagicMock(return_value=None)
        mock_db.return_value = mock_connection

        response = client.post("/delete/999")
        assert response.status_code == 404

    def test_delete_invalid_id(self, client):
        """Test delete with invalid task ID (Flask won't match negative int in route)"""
        response = client.post("/delete/-1")
        assert response.status_code == 404


@pytest.fixture(scope="session")
def db_session():
    """Create database connection for integration tests"""
    try:
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            user=os.environ.get("DB_USER", "user"),
            password=os.environ.get("DB_PASSWORD", "pass"),
            database=os.environ.get("DB_NAME", "todo"),
        )
        yield conn
        conn.close()
    except MySQLError as e:
        pytest.skip(f"Database not available: {e}")


@pytest.fixture
def clean_db(db_session):
    """Clean database before and after each integration test"""
    cursor = db_session.cursor()
    cursor.execute("DELETE FROM todos")
    db_session.commit()
    yield
    cursor.execute("DELETE FROM todos")
    db_session.commit()
    cursor.close()


@pytest.mark.integration
class TestEndToEndUserJourney:
    """Complete user journey testing database integration"""

    def test_complete_user_workflow(self, clean_db, db_session):
        """E2E: Create, complete, and delete tasks"""
        cursor = db_session.cursor(dictionary=True)

        # Create 2 tasks
        cursor.execute(
            "INSERT INTO todos (task, status) VALUES (%s, %s)",
            ("Buy groceries", "pending"),
        )
        task1_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO todos (task, status) VALUES (%s, %s)", ("Read book", "pending")
        )
        db_session.commit()

        # Verify both exist
        cursor.execute("SELECT COUNT(*) as count FROM todos")
        assert cursor.fetchone()["count"] == 2

        # Complete and delete first task
        cursor.execute(
            "UPDATE todos SET status = %s WHERE id = %s", ("completed", task1_id)
        )
        cursor.execute("DELETE FROM todos WHERE id = %s", (task1_id,))
        db_session.commit()

        # Verify only second task remains
        cursor.execute("SELECT task FROM todos")
        assert cursor.fetchone()["task"] == "Read book"
        cursor.close()

    def test_task_creation_and_retrieval(self, clean_db, db_session):
        """E2E: Create and retrieve multiple tasks"""
        cursor = db_session.cursor(dictionary=True)

        for i in range(1, 6):
            cursor.execute(
                "INSERT INTO todos (task, status) VALUES (%s, %s)",
                (f"Task {i}", "pending"),
            )
        db_session.commit()

        cursor.execute("SELECT COUNT(*) as count FROM todos")
        assert cursor.fetchone()["count"] == 5
        cursor.close()

    def test_task_status_transitions(self, clean_db, db_session):
        """E2E: Test all status transitions"""
        cursor = db_session.cursor(dictionary=True)

        cursor.execute(
            "INSERT INTO todos (task, status) VALUES (%s, %s)",
            ("Transition task", "pending"),
        )
        task_id = cursor.lastrowid
        db_session.commit()

        for status in ["completed", "archived"]:
            cursor.execute(
                "UPDATE todos SET status = %s WHERE id = %s", (status, task_id)
            )
            db_session.commit()
            cursor.execute("SELECT status FROM todos WHERE id = %s", (task_id,))
            assert cursor.fetchone()["status"] == status

        cursor.close()

    def test_concurrent_task_operations(self, clean_db, db_session):
        """E2E: Simulate concurrent operations"""
        cursor = db_session.cursor(dictionary=True)

        # Create, update, and delete
        cursor.execute(
            "INSERT INTO todos (task, status) VALUES (%s, %s)", ("Task 1", "pending")
        )
        id1 = cursor.lastrowid
        cursor.execute(
            "INSERT INTO todos (task, status) VALUES (%s, %s)", ("Task 2", "pending")
        )
        id2 = cursor.lastrowid
        cursor.execute(
            "INSERT INTO todos (task, status) VALUES (%s, %s)", ("Task 3", "pending")
        )
        db_session.commit()

        cursor.execute("UPDATE todos SET status = %s WHERE id = %s", ("completed", id1))
        cursor.execute("DELETE FROM todos WHERE id = %s", (id2,))
        db_session.commit()

        cursor.execute("SELECT COUNT(*) as count FROM todos")
        assert cursor.fetchone()["count"] == 2
        cursor.close()


class TestBrowserFormEndpoint:
    """Test the browser form endpoint for adding tasks"""

    def test_add_from_browser_success(self, client):
        """Test adding task via browser form"""
        with patch("app.get_db") as mock_get_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.lastrowid = 42
            mock_conn.cursor.return_value = mock_cursor
            mock_get_db.return_value.__enter__.return_value = mock_conn
            mock_get_db.return_value.__exit__.return_value = False

            response = client.post("/add_from_browser", data={"task": "Browser task"})
            assert response.status_code == 200
            assert (
                b"Task added successfully" in response.data
                or b"task" in response.data.lower()
            )

    def test_add_from_browser_empty_task(self, client):
        """Test browser form with empty task"""
        response = client.post("/add_from_browser", data={"task": ""})
        assert response.status_code == 400

    def test_add_from_browser_no_task_field(self, client):
        """Test browser form without task field"""
        response = client.post("/add_from_browser", data={})
        assert response.status_code == 400


class TestErrorHandlingPaths:
    """Test error handling in various endpoints"""

    def test_complete_task_db_error(self, client):
        """Test complete endpoint with database error"""
        with patch("app.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.side_effect = Exception(
                "DB Connection failed"
            )

            response = client.post("/complete/1")
            assert response.status_code == 500
            data = json.loads(response.data)
            assert "error" in data

    def test_delete_task_db_error(self, client):
        """Test delete endpoint with database error"""
        with patch("app.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.side_effect = Exception(
                "DB Connection failed"
            )

            response = client.post("/delete/1")
            assert response.status_code == 500
            data = json.loads(response.data)
            assert "error" in data

    def test_list_db_error(self, client):
        """Test list endpoint with database error"""
        with patch("app.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.side_effect = Exception(
                "DB Connection failed"
            )

            response = client.get("/list")
            assert response.status_code == 500

    def test_tasks_api_db_error(self, client):
        """Test tasks API endpoint with database error"""
        with patch("app.get_db") as mock_get_db:
            mock_get_db.return_value.__enter__.side_effect = Exception(
                "DB Connection failed"
            )

            response = client.get("/tasks")
            assert response.status_code == 500
            data = json.loads(response.data)
            assert "error" in data
