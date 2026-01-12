docker buildx build ../../backend -t backendimage:1.0.2
minikube image load backendimage:1.0.2