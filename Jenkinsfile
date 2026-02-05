pipeline {
    agent none
    
    environment {
        DOCKER_IMAGE = "todo-app:${BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            agent { label 'docker' }
            steps {
                echo "Checking out code on agent with 'docker' label"
                checkout scm
            }
        }
        
        stage('Unit Tests') {
            agent { label 'testing' }
            steps {
                echo "Running unit tests on agent with 'testing' label"
                sh '''
                    docker-compose down -v
                    docker-compose build
                    docker-compose up -d
                    sleep 15
                    docker-compose exec -T web pytest test_app.py -v -m "not integration" --cov=app
                '''
            }
        }
        
        stage('Integration Tests') {
            agent { label 'testing' }
            steps {
                echo "Running integration tests on agent with 'testing' label"
                sh '''
                    docker-compose exec -T web pytest test_app.py -v -m "integration"
                '''
            }
        }
        
        stage('Code Quality') {
            agent { label 'testing' }
            steps {
                echo "Running code quality checks on agent with 'testing' label"
                sh '''
                    docker-compose exec -T web pip install flake8 black
                    docker-compose exec -T web black --check .
                    docker-compose exec -T web flake8 . --max-line-length=127
                '''
            }
        }
        
        stage('Build Docker Image') {
            agent { label 'build' }
            steps {
                echo "Building Docker image on agent with 'build' label"
                sh '''
                    docker build -t ${DOCKER_IMAGE} -f web/Dockerfile web/
                    docker tag ${DOCKER_IMAGE} todo-app:latest
                '''
            }
        }
    }
    
    post {
        always {
            node('docker') {
                echo "Pipeline completed - Cleaning up"
                sh 'docker-compose down || true'
            }
        }
        success {
            echo "Pipeline succeeded"
        }
        failure {
            echo "Pipeline failed"
        }
    }
}