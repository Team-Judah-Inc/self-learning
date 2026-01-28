#!/bin/bash
PROJECT_ROOT="/Users/tzichlinsky/dev/self-learning"
VALUES_FILE="$PROJECT_ROOT/infra/selflearningchart/values.yaml"

# Extract ports from values.yaml using grep and awk
BACKEND_PORT=$(grep "backendPort:" "$VALUES_FILE" | awk '{print $2}')
FRONTEND_PORT=$(grep "frontendPort:" "$VALUES_FILE" | awk '{print $2}')

# Build and load Backend
docker buildx build $PROJECT_ROOT/backend -t backend:1.0.2 --build-arg PORT=$BACKEND_PORT && minikube image load backend:1.0.2

# Build and load Frontend
docker buildx build $PROJECT_ROOT/frontend -t ui:1.0.0 --build-arg PORT=$FRONTEND_PORT && minikube image load ui:1.0.0
