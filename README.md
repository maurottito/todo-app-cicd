# Todo App with CI/CD

A simple todo application with Flask, MySQL, Nginx, and CI/CD using Jenkins

## Setup instructions

```bash
# Clone and start with Docker Compose
git clone this_repo
cd todo-app-cicd
docker-compose up --build
```

The app will be available at `http://localhost`

## Project Structure

```
├── web/                # Flask app, tests, requirements
├── nginx/              # Reverse proxy config
├── db/                 # Database schema
├── docker-compose.yml  # 3-service stack (MySQL, Flask, Nginx)
├── .gitignore          # Python + CI workflow ignores
└── README.md           # This file
```

## API Endpoints

- `GET /` - Web interface with add task form
- `GET /health` - Health check
- `POST /add` - Add task (JSON: `{"task": "..."}`)
- `GET /tasks` - Get all tasks with pagination
- `GET /list` - Get all tasks as HTML
- `POST/GET /complete/<id>` - Mark task complete
- `POST/GET /delete/<id>` - Delete task

## CI/CD Pipelines

- Unit tests with mocked database (36 tests)
- Integration tests with real MySQL database
- 81% code coverage validation
- Docker image build and validation

## Testing

```bash
# Run all tests (36 tests, 81% coverage)
docker-compose exec web pytest test_app.py -v

# Run with coverage report
docker-compose exec web pytest test_app.py --cov=app --cov-report=term-missing

# Run only unit tests (mocked DB)
docker-compose exec web pytest test_app.py -m "not integration"

# Run only integration tests (real DB)
docker-compose exec web pytest test_app.py -m "integration"
```
