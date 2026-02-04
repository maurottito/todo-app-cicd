pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = "todo-app:${BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo "Checking out code"
                checkout scm
            }
        }
        
        stage('Unit Tests') {
            steps {
                echo "Running unit tests in Docker"
                sh '''
                    docker-compose up -d
                    sleep 15
                    docker-compose exec -T web pytest test_app.py -v -m "not integration" --cov=app
                '''
            }
        }
        
        stage('Integration Tests') {
            steps {
                echo "Running integration tests in Docker"
                sh '''
                    docker-compose exec -T web pytest test_app.py -v -m "integration"
                '''
            }
        }
        
        stage('Code Quality') {
            steps {
                echo "Code quality checks in Docker"
                sh '''
                    docker-compose exec -T web pip install flake8 black
                    docker-compose exec -T web black --check web/
                    docker-compose exec -T web flake8 web/ --max-line-length=127
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
            echo "Pipeline completed - Cleaning up"
            sh 'docker-compose down || true'
        }
        success {
            echo "Pipeline succeeded"
        }
        failure {
            echo "Pipeline failed"
        }
    }
}