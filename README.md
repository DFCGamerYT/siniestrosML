# Siniestros ML

Microservicio FastAPI para predecir la gravedad de siniestros en Bogotá.  
Este README resume la instalación y despliegue mediante Kubernetes (Helm), CI con Jenkins y entrega GitOps con Argo CD.

## Resumen rápido
- App: FastAPI en `app/`
- Dockerfile: `Dockerfile`
- Helm chart: `siniestros-ml-chart/`
- Pipeline CI: `Jenkinsfile` (construye imagen, la publica en Docker Hub y actualiza `values.yaml`)
- Argo CD: `deploy/argocd/application.yaml` (aplica el chart desde el repo)

## Requisitos
- kubectl >= 1.20
- Helm >= 3
- Docker CLI (para build/push)
- Jenkins (servidor) o acceso a la instancia de CI
- Argo CD (control plane en el clúster)
- Credenciales para push de imágenes (Docker Hub / Registry)

## Instalación en Kubernetes (Helm)
1. Construir y publicar la imagen (local o CI):
   - Local:
     - docker build -t DOCKER_USER/siniestros-ml:TAG .
     - docker push DOCKER_USER/siniestros-ml:TAG
   - En CI: el `Jenkinsfile` del repo realiza build/push y actualiza `siniestros-ml-chart/values.yaml`.

2. Desplegar el chart con Helm:
   - Cambiar `image.repository` y `image.tag` en `siniestros-ml-chart/values.yaml` o pasar parámetros al instalar:
     - helm install siniestros-ml ./siniestros-ml-chart -n siniestros-ml --create-namespace --set image.repository=DOCKER_USER/siniestros-ml --set image.tag=TAG
   - Para actualizar:
     - helm upgrade siniestros-ml ./siniestros-ml-chart -n siniestros-ml --set image.tag=NEW_TAG

3. Comprobar despliegue:
   - kubectl -n siniestros-ml get pods,svc
   - kubectl -n siniestros-ml logs deploy/siniestros-ml

Notas:
- Asegurar un Secret para imagePullSecrets si el registry es privado.
- El chart incluye liveness/readiness probes y ConfigMap para configuración.

## Jenkins (pipeline)
- El `Jenkinsfile` hace:
  1. Checkout del repo (branch `main`).
  2. Build de la imagen Docker.
  3. Push a Docker Hub (credenciales gestionadas en Jenkins).
  4. Actualiza `siniestros-ml-chart/values.yaml` con el nuevo tag y hace commit/push al repo.
- Para instalar Jenkins en Kubernetes (opcional, ejemplo con Helm chart oficial):
  - helm repo add jenkins https://charts.jenkins.io
  - helm repo update
  - helm install jenkins jenkins/jenkins -n jenkins --create-namespace
- Configurar credenciales en Jenkins:
  - Credenciales Docker Hub (ID usado en `Jenkinsfile`: `docker-hub-credentials`)
  - Credenciales para push al repo Git (ID `github-path` en el `Jenkinsfile`)

## Argo CD (GitOps)
- Patrón: Argo CD apunta al chart en este repo y sincroniza el estado del clúster con `siniestros-ml-chart`.
- Aplicar la Application (ejemplo localizado en `deploy/argocd/application.yaml`):
  - kubectl apply -f deploy/argocd/application.yaml -n argocd
- Recomendaciones:
  - Configurar `image.repository` y `image.tag` en `values.yaml`. El pipeline (Jenkins) actualiza `image.tag` y Argo CD hará sync automático si está habilitado.
  - Habilitar `CreateNamespace=true` si la App debe crear su namespace.
  - Usar Argo CD RBAC y SSO para controlar accesos.

## Endpoints importantes
- POST /ml/predecir  — predicción
- GET /health        — health check
- GET /health/metrics — métricas

## Flujo CI/CD (resumen)
1. Código o cambios en `main`.
2. Jenkins ejecuta `Jenkinsfile`: build -> push imagen -> bump tag en `values.yaml` -> push commit.
3. Argo CD detecta cambio en Git y sincroniza el cluster aplicando el Helm chart con el nuevo tag.

