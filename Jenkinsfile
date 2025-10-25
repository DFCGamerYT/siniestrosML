pipeline {
    agent any
    environment {
        DOCKER_IMAGE = "mrraiikiri/siniestros-ml:${env.BUILD_NUMBER}"
    }
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/DFCGamerYT/siniestrosML.git'
            }
        }
        stage('Unit Tests') {
            steps {
                script {
                    sh "pip install pytest pytest-mock"
                    sh "pytest app"
                }
            }
        }
        stage('Build Docker Image') {
            steps {
                script {
                    dockerImage = docker.build("${DOCKER_IMAGE}")
                }
            }
        }
        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry('', 'docker-hub-credentials') {
                        dockerImage.push()
                    }
                }
            }
        }
    }
}