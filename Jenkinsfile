pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = "todo-app:${BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo "📦 Checking out code"
                checkout scm
            }
        }
        
        stage('Unit Tests') {
            steps {
                echo "Running unit tests"
                sh '''
                    cd web
                    pip install -r requirements.txt
                    pytest test_app.py -v -m "not integration" --cov=app
                '''
            }
        }
        
        stage('Integration Tests') {
            steps {
                echo "Running integration tests"
                sh '''
                    cd web
                    # Start MySQL for integration tests
                    docker-compose up -d db
                    sleep 10
                    pytest test_app.py -v -m "integration"
                '''
            }
        }
        
        stage('Code Quality') {
            steps {
                echo "Running code quality checks"
                sh '''
                    cd web
                    pip install flake8 black
                    black --check .
                    flake8 . --max-line-length=127
                '''
            }
        }
        
        stage('Build Docker Image') {
            steps {
                echo "Building Docker image"
                sh '''
                    docker build -t ${DOCKER_IMAGE} -f web/Dockerfile web/
                    docker tag ${DOCKER_IMAGE} todo-app:latest
                '''
            }
        }
    }
    
    post {
        always {
            echo "Pipeline completed"
            // Cleanup
            sh 'docker-compose down || true'
        }
        success {
            echo "Pipeline succeeded!"
        }
        failure {
            echo "Pipeline failed!"
        }
    }
}