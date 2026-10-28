.PHONY: build up down stop restart logs status test docs

COMPOSE = docker compose
SERVICE = nagrik-ai-local
PORT = 5000
BASE_URL = http://localhost:$(PORT)

# Build the local image and start in the background
build:
	$(COMPOSE) up -d --build

# Start the application in the foreground
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

# Follow application logs
logs:
	$(COMPOSE) logs -f $(SERVICE)

# Show container status
status:
	$(COMPOSE) ps

# Test the health endpoint
test:
	curl -f $(BASE_URL)/health

# Open Swagger UI in the browser (Linux)
docs:
	xdg-open $(BASE_URL)/docs