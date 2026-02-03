# Todo App with CI/CD

A simple todo application with Flask, MySQL, Nginx, and GitHub Actions CI/CD.

## Setup instructions

```bash
# Clone and start with Docker Compose
git clone this_repo
cd todo-app-ci
docker-compose up --build
```

The app will be available at `http://localhost`

## Project Structure

```
.
├── web/                # Flask app, tests
├── nginx/              # Reverse proxy config
├── db/                 # Database schema
├── docker-compose.yml  # Multi-container setup
└── .github/workflows/  # CI/CD pipelines
```

## API Endpoints

- `GET /health` - Health check
- `GET /` - Web interface
- `POST /add` - Add task (JSON): `{"task": "..."}`
- `GET /list` - Get all tasks
- `GET /delete/<id>` - Delete task
- `POST /add_from_browser` - Add via form

## CI/CD Pipelines

1. Python Test Job
   - Black formatting check
   - flake8 linting
   - pytest with >80% code coverage
   - Uploads coverage reports
   - Triggered on push/PR to main

2. Docker Build Job
   - Runs after Python tests pass
   - Dockerfile syntax validation
   - Docker image build and test
   - Triggered on push/PR to main
