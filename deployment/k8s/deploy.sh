#!/bin/bash

set -e

echo "🚀 Deploying TraderTerminal to Kubernetes..."

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if we can connect to a cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster. Please configure kubectl."
    exit 1
fi

echo "✅ Kubernetes cluster connection verified"

# Create namespace
echo "📦 Creating namespace..."
kubectl apply -f 00-namespace.yaml

# Apply configs
echo "⚙️  Applying configuration..."
kubectl apply -f 01-configmap.yaml

# Check if secrets exist, if not warn user
if ! kubectl get secret traderterminal-secrets -n traderterminal &> /dev/null; then
    echo "⚠️  WARNING: traderterminal-secrets not found!"
    echo "   Please create secrets from template:"
    echo "   1. Copy 05-secrets-template.yaml to 05-secrets.yaml"
    echo "   2. Replace template values with real credentials"
    echo "   3. Run: kubectl apply -f 05-secrets.yaml"
    echo ""
    echo "   Continuing deployment without secrets (some features will be disabled)..."
else
    echo "✅ Secrets found"
fi

# Deploy application
echo "🚢 Deploying application..."
kubectl apply -f 02-deployment.yaml
kubectl apply -f 03-service.yaml
kubectl apply -f 04-ingress.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl -n traderterminal rollout status deployment/traderterminal-api --timeout=300s

# Check pod status
echo "📊 Pod status:"
kubectl -n traderterminal get pods

# Get service information
echo "🌐 Service information:"
kubectl -n traderterminal get svc

# Get ingress information
echo "🚪 Ingress information:"
kubectl -n traderterminal get ingress

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "   • Add 'traderterminal.local' to your /etc/hosts file pointing to your ingress IP"
echo "   • Access the application at: http://traderterminal.local"
echo "   • Monitor with: kubectl -n traderterminal get pods -w"
echo "   • View logs with: kubectl -n traderterminal logs -f deployment/traderterminal-api"