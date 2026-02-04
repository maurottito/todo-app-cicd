import os
import logging
from contextlib import contextmanager
from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error as MySQLError

# logging
log_dir = "/app/logs"
try:
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
except PermissionError:
    log_dir = "/tmp/logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

logging.basicConfig(
    filename=os.path.join(log_dir, "app.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)

app = Flask(__name__)


def get_db_connection():
    """Create and return a MySQL connection"""
    try:
        return mysql.connector.connect(
            host=os.environ["DB_HOST"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
        )
    except MySQLError as e:
        logging.error(f"Database connection failed: {e}")
        raise


@contextmanager
def get_db():
    """Context manager for safe database connections and transactions"""
    conn = None
    try:
        conn = get_db_connection()
        yield conn
        conn.commit()
    except MySQLError as e:
        if conn:
            conn.rollback()
        logging.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def validate_task(task):
    """Validate task input"""
    if not task or not isinstance(task, str):
        raise ValueError("Task must be a non-empty string")
    task = task.strip()
    if not task:
        raise ValueError("Task cannot be empty or whitespace only")
    if len(task) > 255:
        raise ValueError("Task must be 255 characters or less")
    return task


@app.route("/")
def index():
    """Render home page with add task form"""
    logging.info("Index page accessed")
    return """
        <h1>Todo API</h1>
        <form action="/add_from_browser" method="post">
            <input type="text" name="task" placeholder="Enter a task" required>
            <button type="submit">Add Task</button>
        </form>
        <br>
        <a href="/list"><button>View All Tasks</button></a>
    """


@app.route("/health")
def health():
    """Health check endpoint"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


@app.route("/add", methods=["POST"])
def add():
    """API endpoint to add a task (JSON)"""
    try:
        try:
            data = request.get_json()
        except Exception:
            return jsonify({"error": "Request body must be JSON"}), 400

        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        task = data.get("task")
        task = validate_task(task)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO todos (task, status) VALUES (%s, %s)",
                (task, "pending")
            )
            task_id = cursor.lastrowid

        logging.info(f"Task added: {task_id}")
        return jsonify({
            "message": "Task added successfully",
            "task_id": task_id,
            "task": task,
            "status": "pending"
        }), 201

    except ValueError as e:
        logging.warning(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
    except MySQLError as e:
        logging.error(f"Database error in /add: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        logging.error(f"Unexpected error in /add: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/add_from_browser", methods=["POST"])
def add_from_browser():
    """Browser form endpoint to add a task"""
    try:
        task = request.form.get("task")
        task = validate_task(task)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO todos (task, status) VALUES (%s, %s)",
                (task, "pending")
            )

        logging.info(f"Task added from browser: {task}")
        return f'<h2>Added "{task}"!</h2> <a href="/">Go back</a>'

    except ValueError as e:
        logging.warning(f"Validation error: {e}")
        return f'<h2>Error: {str(e)}</h2> <a href="/">Go back</a>', 400
    except MySQLError as e:
        logging.error(f"Database error in /add_from_browser: {e}")
        return "<h2>Database error occurred</h2> <a href=\"/\">Go back</a>", 500
    except Exception as e:
        logging.error(f"Unexpected error in /add_from_browser: {e}")
        return "<h2>An error occurred</h2> <a href=\"/\">Go back</a>", 500


@app.route("/list")
def list_all():
    """Get all tasks (HTML view)"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, task, status FROM todos")
            tasks = cursor.fetchall()

        html = """
            <h1>Todo List</h1>
            <table border="1" cellpadding="10">
                <tr><th>ID</th><th>Task</th><th>Status</th><th>Actions</th></tr>
        """
        for task_id, task_text, status in tasks:
            action_buttons = f'<a href="/delete/{task_id}">Delete</a>'
            if status == "pending":
                action_buttons += f' | <a href="/complete/{task_id}">Mark Complete</a>'
            html += f"<tr><td>{task_id}</td><td>{task_text}</td><td>{status}</td><td>{action_buttons}</td></tr>"

        html += """
            </table>
            <br><a href="/"><button>Back</button></a>
        """
        return html

    except MySQLError as e:
        logging.error(f"Database error in /list: {e}")
        return "<h2>Database error occurred</h2>", 500
    except Exception as e:
        logging.error(f"Unexpected error in /list: {e}")
        return "<h2>An error occurred</h2>", 500


@app.route("/tasks", methods=["GET"])
def get_tasks_api():
    """API endpoint to get all tasks (JSON) - Returns all tasks with pagination support"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        status_filter = request.args.get("status", type=str)

        if page < 1 or per_page < 1 or per_page > 100:
            return jsonify({"error": "Invalid pagination parameters"}), 400

        offset = (page - 1) * per_page

        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)

            # Build query based on filters
            query = "SELECT id, task, status FROM todos"
            params = []
            if status_filter:
                query += " WHERE status = %s"
                params.append(status_filter)

            query += " LIMIT %s OFFSET %s"
            params.extend([per_page, offset])

            cursor.execute(query, params)
            tasks = cursor.fetchall()

        logging.info(f"Retrieved {len(tasks)} tasks from page {page}")
        return jsonify({
            "page": page,
            "per_page": per_page,
            "count": len(tasks),
            "tasks": tasks
        }), 200

    except MySQLError as e:
        logging.error(f"Database error in /tasks: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        logging.error(f"Unexpected error in /tasks: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/complete/<int:task_id>", methods=["POST", "GET"])
def complete_task(task_id):
    """Mark a task as completed"""
    try:
        if task_id < 1:
            return jsonify({"error": "Invalid task ID"}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            # Check if task exists
            cursor.execute("SELECT id FROM todos WHERE id = %s", (task_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Task not found"}), 404

            # Update task status
            cursor.execute(
                "UPDATE todos SET status = %s WHERE id = %s",
                ("completed", task_id)
            )

        logging.info(f"Task marked complete: {task_id}")
        if request.method == "GET":
            return f'<h2>Task marked complete!</h2> <a href="/list">Back to list</a>'
        return jsonify({"message": "Task marked complete", "task_id": task_id}), 200

    except MySQLError as e:
        logging.error(f"Database error in /complete: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        logging.error(f"Unexpected error in /complete: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/delete/<int:task_id>", methods=["POST", "GET"])
def delete(task_id):
    """Delete a task by ID"""
    try:
        if task_id < 1:
            return jsonify({"error": "Invalid task ID"}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            # Check if task exists
            cursor.execute("SELECT id FROM todos WHERE id = %s", (task_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Task not found"}), 404

            # Delete task
            cursor.execute("DELETE FROM todos WHERE id = %s", (task_id,))

        logging.info(f"Task deleted: {task_id}")
        if request.method == "GET":
            return f'<h2>Task deleted!</h2> <a href="/list">Back to list</a>'
        return jsonify({"message": "Task deleted", "task_id": task_id}), 200

    except MySQLError as e:
        logging.error(f"Database error in /delete: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        logging.error(f"Unexpected error in /delete: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logging.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
