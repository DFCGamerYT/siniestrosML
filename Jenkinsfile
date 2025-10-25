pipeline {
    agent any

    environment {
        REGISTRY_REPO = "mrraiikiri/siniestros-ml"
        IMAGE_TAG     = "${env.BUILD_NUMBER}"
        DOCKER_IMAGE  = "${REGISTRY_REPO}:${IMAGE_TAG}"
        VALUES_PATH   = "siniestros-ml-chart/values.yaml"
        GIT_USER_NAME = "jenkins-bot"
        GIT_USER_MAIL = "jenkins-bot@local"
        GITHUB_REPO   = "DFCGamerYT/siniestrosML"
        MAIN_BRANCH   = "main"
    }

    options { timestamps() }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/DFCGamerYT/siniestrosML.git'
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

        stage('Bump Helm tag in values.yaml') {
            steps {
                powershell '''
                    (Get-Content "${env:VALUES_PATH}") -replace '(^\\s*tag:\\s*).+', "``tag:${env:IMAGE_TAG}" | Set-Content "${env:VALUES_PATH}"
                    Write-Host ">>> Diff:"
                    git --no-pager diff -- "${env:VALUES_PATH}"
                '''
            }
        }
 
        stage('Commit & Push change') {
            steps {
                bat """
                    git config user.name  "${GIT_USER_NAME}"
                    git config user.email "${GIT_USER_MAIL}"
                    git add "${VALUES_PATH}"
                    git commit -m "[skip ci] chore(helm): bump image tag to ${IMAGE_TAG}" || (
                    echo "No hay cambios que commitear"
                    exit /b 0
                    )
                """
                withCredentials([string(credentialsId: 'github-path', variable: 'GIT_PATH')]) {
                    bat """
                        git remote set-url origin https://${GIT_PATH}@github.com/${GITHUB_REPO}.git
                        git push origin HEAD:${MAIN_BRANCH}
                    """
                }
            }
        }
    }

    post {
        success {
            echo "OK ✅ Imagen publicada: ${DOCKER_IMAGE} y values.yaml actualizado"
        }
        failure {
            echo "❌ Pipeline falló"
        }
    }
}
