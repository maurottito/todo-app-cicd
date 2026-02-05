import requests
import time


def test_complete_user_journey():
    """
    E2E test simulating complete user workflow using API calls
    """
    base_url = "http://localhost:5000"

    # Test home page
    print("Testing home page")
    response = requests.get(base_url)
    assert response.status_code == 200
    assert "Todo API" in response.text

    # Add a new task
    print("Adding a new task via API")
    task_name = f"E2E Test Task {int(time.time())}"
    response = requests.post(
        f"{base_url}/add",
        json={"task": task_name},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code in [200, 201]
    response_data = response.json()
    assert "task_id" in response_data
    task_id = response_data["task_id"]
    print(f"Task added with ID: {task_id}")

    # View all tasks via API endpoint
    print("Viewing all tasks via /tasks endpoint")
    response = requests.get(f"{base_url}/tasks")
    assert response.status_code == 200
    response_data = response.json()
    assert "tasks" in response_data
    tasks = response_data["tasks"]
    assert isinstance(tasks, list)

    # Verify our task is in the list
    task_found = any(task["id"] == task_id for task in tasks)
    assert task_found, f"Task with ID {task_id} not found in task list"
    print("Task verified in list")

    # Complete the task
    print(f"Completing task ID {task_id}")
    response = requests.post(f"{base_url}/complete/{task_id}")
    assert response.status_code == 200

    # Verify task is marked as completed
    response = requests.get(f"{base_url}/tasks")
    response_data = response.json()
    tasks = response_data["tasks"]
    for task in tasks:
        if task["id"] == task_id:
            assert task["status"] == "completed"
            print("Task successfully marked as completed")

    print("End-to-end test completed successfully!")


def test_health_check():
    """Test that API health endpoint is accessible"""
    base_url = "http://localhost:5000"

    print("Testing health endpoint")
    response = requests.get(f"{base_url}/health")
    assert response.status_code == 200

    content = response.text.lower()
    assert "healthy" in content

    print("Health check test passed")
