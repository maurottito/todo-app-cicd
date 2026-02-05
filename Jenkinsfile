pipeline {
    agent none
    
    environment {
        DOCKER_IMAGE = "todo-app-cicd:${BUILD_NUMBER}"
        VERSION = "${BUILD_NUMBER}"
        ARTIFACT_NAME = "todo-app-cicd-v${BUILD_NUMBER}.tar.gz"
    }
    
    // Webhook triggers
    triggers {
        pollSCM('H/5 * * * *')
    }
    
    stages {
        stage('Checkout') {
            agent { label 'docker' }
            steps {
                echo "Checking out code on agent with 'docker' label"
                echo "Branch: ${env.BRANCH_NAME}"
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
            when {
                branch 'main'
            }
            agent { label 'build' }
            steps {
                echo "Building Docker image - Version: v${VERSION}"
                sh '''
                    docker build -t ${DOCKER_IMAGE} -f web/Dockerfile web/
                    docker tag ${DOCKER_IMAGE} todo-app-cicd:latest
                    docker tag ${DOCKER_IMAGE} todo-app-cicd:v${VERSION}
                '''
            }
        }
        
        stage('Package Artifacts') {
            when {
                branch 'main'
            }
            agent { label 'build' }
            steps {
                echo "Creating versioned artifacts"
                sh '''
                    # Package application source
                    tar -czf ${ARTIFACT_NAME} web/ docker-compose.yml
                    
                    # Create build info
                    echo "Version: v${VERSION}" > build-info.txt
                    echo "Build: ${BUILD_NUMBER}" >> build-info.txt
                    echo "Date: $(date)" >> build-info.txt
                    
                    ls -lh ${ARTIFACT_NAME}
                '''
                archiveArtifacts artifacts: '*.tar.gz, build-info.txt', fingerprint: true
                echo "Artifacts archived: ${ARTIFACT_NAME}"
            }
        }
        
        stage('Deploy') {
            when {
                branch 'main'
            }
            agent { label 'deployment' }
            steps {
                echo "Deploying version: v${VERSION}"
                sh '''
                    echo "Docker image: ${DOCKER_IMAGE}"
                    echo "Version: v${VERSION}"
                    docker images | grep todo-app-cicd
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
            script {
                def message = """
                    :white_check_mark: *Pipeline Success*
                    *Job:* ${env.JOB_NAME}
                    *Build:* #${env.BUILD_NUMBER}
                    *Branch:* ${env.BRANCH_NAME}
                    *Version:* v${VERSION}
                    *Duration:* ${currentBuild.durationString.replace(' and counting', '')}
                    *Status:* SUCCESS
                    <${env.BUILD_URL}|View Build>
                """.stripIndent()
                
                echo "Pipeline succeeded - Version: v${VERSION}"
                
                slackSend(
                    color: 'good',
                    message: message,
                    channel: '#devops-notifications'
                )
            }
        }
        failure {
            script {
                def message = """
                    :x: *Pipeline Failed*
                    *Job:* ${env.JOB_NAME}
                    *Build:* #${env.BUILD_NUMBER}
                    *Branch:* ${env.BRANCH_NAME}
                    *Version:* v${VERSION}
                    *Duration:* ${currentBuild.durationString.replace(' and counting', '')}
                    *Status:* FAILED
                    *Error:* ${currentBuild.description ?: 'Check build logs for details'}
                    <${env.BUILD_URL}console|View Console Output>
                """.stripIndent()
                
                echo "Pipeline failed"
                
                slackSend(
                    color: 'danger',
                    message: message,
                    channel: '#devops-notifications'
                )
            }
        }
    }
}
