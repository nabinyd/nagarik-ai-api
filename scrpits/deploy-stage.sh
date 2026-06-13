#!/bin/bash
set -e

echo "🚀 Starting FastAPI Staging Deployment..."

# Configuration
REPO_URL="git@github.com:nabinyd/nagarik-ai-api.git"
BRANCH="stage"
DEPLOY_DIR="/home/ubuntu/nagrik-ai-api"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"; }
warn() { echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN:${NC} $1"; }
error() { echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"; exit 1; }

# Test GitHub SSH
log "Testing SSH connection to GitHub..."
ssh -T git@github.com || true

# Clone or Update Repository
if [ ! -d "$DEPLOY_DIR" ]; then
    log "Repository not found. Cloning..."
    mkdir -p "$DEPLOY_DIR"
    git clone -b "$BRANCH" "$REPO_URL" "$DEPLOY_DIR"
else
    cd "$DEPLOY_DIR"

    if [ ! -d ".git" ]; then
        warn "Directory exists but is not a git repository. Re-cloning..."
        cd /home/ubuntu
        rm -rf nagrik-ai-api
        git clone -b "$BRANCH" "$REPO_URL" "$DEPLOY_DIR"
    else
        log "Pulling latest code..."
        git fetch origin
        git checkout "$BRANCH"
        git pull origin "$BRANCH"
        log "✅ Code updated successfully"
    fi
fi

cd "$DEPLOY_DIR"

# Create .env.staging
log "Creating environment configuration..."

cat > .env.staging << EOF
GROQ_API_KEY=${GROQ_API_KEY}
GROQ_MODEL=${GROQ_MODEL}
GROQ_TEMPERATURE=${GROQ_TEMPERATURE}

QDRANT_URL=${QDRANT_URL}
QDRANT_API_KEY=${QDRANT_API_KEY}
COLLECTION_NAME=${COLLECTION_NAME}

GEMINI_API_KEY=${GEMINI_API_KEY}
GEMINI_MODEL=${GEMINI_MODEL}
GEMINI_TEMPERATURE=${GEMINI_TEMPERATURE}

EMBEDDING_MODEL=${EMBEDDING_MODEL}

DEBUG=${DEBUG}

HOST=0.0.0.0
PORT=5000

TOP_K_RESULTS=${TOP_K_RESULTS}

RATE_LIMIT=${RATE_LIMIT}
RATE_LIMIT_PERIOD=${RATE_LIMIT_PERIOD}
EOF

log "Environment file created"

# Stop existing containers
log "Stopping existing containers..."

docker compose -f docker-compose.staging.yml down || \
warn "No running containers found."

# Build and Start
log "Building and starting containers..."

docker compose -f docker-compose.staging.yml up -d --build

# Wait
log "Waiting for services to start..."
sleep 20

# Health Check
log "Running health check..."

if curl -f http://localhost:5001/health; then
    log "✅ Health check passed!"
else
    error "❌ Health check failed!"
fi

# Container Status
log "Container Status:"
docker compose -f docker-compose.staging.yml ps

log "✅ FastAPI staging deployment completed successfully!"