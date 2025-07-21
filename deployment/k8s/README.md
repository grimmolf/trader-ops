# Kubernetes Deployment

This directory contains Kubernetes manifests for deploying TraderTerminal in a webserver-first architecture.

## Quick Start

1. **Build the Docker image:**
   ```bash
   npm run docker:build
   ```

2. **Create secrets:**
   ```bash
   cp 05-secrets-template.yaml 05-secrets.yaml
   # Edit 05-secrets.yaml with your actual credentials
   kubectl apply -f 05-secrets.yaml
   ```

3. **Deploy to Kubernetes:**
   ```bash
   ./deploy.sh
   ```

4. **Access the application:**
   - Add `traderterminal.local` to your /etc/hosts file pointing to your ingress IP
   - Visit: http://traderterminal.local

## Files

- `00-namespace.yaml` - Creates the traderterminal namespace
- `01-configmap.yaml` - Application configuration
- `02-deployment.yaml` - Main application deployment
- `03-service.yaml` - ClusterIP service
- `04-ingress.yaml` - Nginx ingress with WebSocket support
- `05-secrets-template.yaml` - Template for secrets (copy and modify)
- `deploy.sh` - Deployment script

## Architecture

The deployment serves the Vue 3 web application directly from the FastAPI backend using static file serving. This enables:

- **Cloud deployment** with Kubernetes scaling
- **Web browser access** without Electron
- **Headless operation** for server environments
- **Single container** with both frontend and backend

## Environment Variables

Key configuration options:

- `STATIC_FILES_ENABLED=true` - Enable web app serving
- `UI_URL` - Override for Electron wrapper
- `WEB_SERVER_URL` - Production web server URL
- `CORS_ORIGINS` - Allowed origins for CORS

## Monitoring

Check deployment status:
```bash
kubectl -n traderterminal get pods -w
kubectl -n traderterminal logs -f deployment/traderterminal-api
```

## Security

- Runs as non-root user (1000:1000)
- Secrets stored in Kubernetes secrets
- CORS properly configured
- Health checks configured