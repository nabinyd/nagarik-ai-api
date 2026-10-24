
.PHONY: build up down stop restart logs status test docs

COMPOSE = docker compose -f docker-compose.staging.yml
SERVICE = nagrik-ai-staging

# Build and start staging in the background
build:
	$(COMPOSE) up -d --build

# Start staging in the background
up:
	$(COMPOSE) up

# Stop and remove containers and networks
down:
	$(COMPOSE) down

# Stop containers without removing them
stop:
	$(COMPOSE) stop

# Restart existing containers
restart:
	$(COMPOSE) restart

# Follow logs
logs:
	$(COMPOSE) logs -f $(SERVICE)

# Show container status
status:
	$(COMPOSE) ps

# Test the health endpoint
test:
	curl -f http://localhost:5001/health

# Open Swagger UI in your browser (Linux)
docs:
	xdg-open http://localhost:5001/docs
