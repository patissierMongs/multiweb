#!/bin/bash

# MultiWeb Kubernetes Setup Script
# Sets up a local Kubernetes cluster using Kind or Minikube

set -e

echo "=========================================="
echo "MultiWeb Kubernetes Setup"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo -e "${GREEN}Detected OS: ${MACHINE}${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo ""
echo "Checking prerequisites..."

if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker installed${NC}"

if ! command_exists kubectl; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ kubectl installed${NC}"

# Choose cluster type
echo ""
echo "Choose Kubernetes cluster type:"
echo "1) Kind (Kubernetes in Docker)"
echo "2) Minikube"
read -p "Enter choice [1-2]: " cluster_choice

case $cluster_choice in
    1)
        CLUSTER_TYPE="kind"
        if ! command_exists kind; then
            echo -e "${YELLOW}Kind not found. Installing...${NC}"
            if [ "$MACHINE" = "Mac" ]; then
                brew install kind
            else
                curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
                chmod +x ./kind
                sudo mv ./kind /usr/local/bin/kind
            fi
        fi
        ;;
    2)
        CLUSTER_TYPE="minikube"
        if ! command_exists minikube; then
            echo -e "${YELLOW}Minikube not found. Installing...${NC}"
            if [ "$MACHINE" = "Mac" ]; then
                brew install minikube
            else
                curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
                sudo install minikube-linux-amd64 /usr/local/bin/minikube
            fi
        fi
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Create cluster
echo ""
echo -e "${GREEN}Creating Kubernetes cluster...${NC}"

if [ "$CLUSTER_TYPE" = "kind" ]; then
    # Check if cluster already exists
    if kind get clusters | grep -q "multiweb"; then
        echo -e "${YELLOW}Cluster 'multiweb' already exists${NC}"
        read -p "Delete and recreate? (y/n): " recreate
        if [ "$recreate" = "y" ]; then
            kind delete cluster --name multiweb
        else
            echo "Using existing cluster"
        fi
    fi

    # Create Kind cluster with custom config
    if ! kind get clusters | grep -q "multiweb"; then
        cat <<EOF | kind create cluster --name multiweb --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
  - containerPort: 30000
    hostPort: 30000
    protocol: TCP
- role: worker
- role: worker
EOF
    fi

    kubectl cluster-info --context kind-multiweb

elif [ "$CLUSTER_TYPE" = "minikube" ]; then
    # Check if cluster is running
    if minikube status | grep -q "Running"; then
        echo -e "${YELLOW}Minikube cluster already running${NC}"
    else
        minikube start --cpus=4 --memory=8192 --disk-size=40g
    fi

    kubectl cluster-info
fi

# Install Nginx Ingress Controller
echo ""
echo -e "${GREEN}Installing Nginx Ingress Controller...${NC}"

if [ "$CLUSTER_TYPE" = "kind" ]; then
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
elif [ "$CLUSTER_TYPE" = "minikube" ]; then
    minikube addons enable ingress
fi

echo "Waiting for Ingress Controller to be ready..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=300s

# Install Metrics Server
echo ""
echo -e "${GREEN}Installing Metrics Server...${NC}"

if [ "$CLUSTER_TYPE" = "minikube" ]; then
    minikube addons enable metrics-server
else
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

    # Patch metrics-server for local development
    kubectl patch deployment metrics-server -n kube-system --type='json' \
      -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
fi

# Create namespace
echo ""
echo -e "${GREEN}Creating MultiWeb namespace...${NC}"
kubectl create namespace multiweb --dry-run=client -o yaml | kubectl apply -f -

# Deploy resources
echo ""
echo -e "${GREEN}Deploying MultiWeb resources...${NC}"

# Apply in order
kubectl apply -f ../k8s/base/namespace.yaml
kubectl apply -f ../k8s/base/configmap.yaml
kubectl apply -f ../k8s/base/secret.yaml
kubectl apply -f ../k8s/base/postgres.yaml
kubectl apply -f ../k8s/base/redis.yaml

# Wait for databases
echo "Waiting for databases to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n multiweb --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n multiweb --timeout=300s

# Deploy monitoring stack
echo ""
echo -e "${GREEN}Deploying monitoring stack...${NC}"
kubectl apply -f ../k8s/monitoring/
kubectl apply -f ../k8s/logging/

# Deploy application
echo ""
echo -e "${GREEN}Building and deploying application...${NC}"

# Build Docker image
cd ../app
docker build -t multiweb-api:latest .

# Load image into cluster
if [ "$CLUSTER_TYPE" = "kind" ]; then
    kind load docker-image multiweb-api:latest --name multiweb
elif [ "$CLUSTER_TYPE" = "minikube" ]; then
    minikube image load multiweb-api:latest
fi

cd ../scripts

# Deploy application
kubectl apply -f ../k8s/base/api.yaml
kubectl apply -f ../k8s/ingress/ingress.yaml

# Wait for application
echo "Waiting for application to be ready..."
kubectl wait --for=condition=ready pod -l app=multiweb-api -n multiweb --timeout=300s

# Print access information
echo ""
echo -e "${GREEN}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Access the application:"
echo "  API: http://localhost:30000"
echo "  Grafana: http://localhost:30001 (admin/admin)"
echo "  Prometheus: http://localhost:30002"
echo ""
echo "Useful commands:"
echo "  kubectl get pods -n multiweb"
echo "  kubectl logs -f deployment/multiweb-api -n multiweb"
echo "  kubectl port-forward svc/grafana 3000:3000 -n multiweb"
echo ""
echo -e "${YELLOW}Note: Update your /etc/hosts file:${NC}"
echo "  127.0.0.1 multiweb.local"
