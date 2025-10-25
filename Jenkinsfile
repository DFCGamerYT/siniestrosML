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
                git branch: env.MAIN_BRANCH, url: "https://github.com/${env.GITHUB_REPO}.git"
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
            environment {
                DOCKERHUB_USER = credentials('docker-hub-credentials_USR')
                DOCKERHUB_PASS = credentials('docker-hub-credentials_PSW')
            }
            steps {
                sh """
                  echo "${DOCKERHUB_PASS}" | docker login -u "${DOCKERHUB_USER}" --password-stdin
                  docker push ${DOCKER_IMAGE}
                """
            }
        }

        stage('Bump Helm tag in values.yaml') {
            steps {
                sh """
                  sed -i -E 's/^(\\s*tag:\\s*).*/\\1${IMAGE_TAG}/' "${VALUES_PATH}"

                  echo ">>> Diff:"
                  git --no-pager diff -- "${VALUES_PATH}"
                """
            }
        }

        stage('Commit & Push change') {
            steps {
                sh """
                  git config user.name  "${GIT_USER_NAME}"
                  git config user.email "${GIT_USER_MAIL}"
                  git add "${VALUES_PATH}"
                  git commit -m "[skip ci] chore(helm): bump image tag to ${IMAGE_TAG}"
                """
                withCredentials([string(credentialsId: 'github-pat', variable: 'GIT_PAT')]) {
                    sh """
                      git remote set-url origin https://${GIT_PAT}@github.com/${GITHUB_REPO}.git
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