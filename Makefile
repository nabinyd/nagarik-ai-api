.PHONY: build up dev watch down stop restart logs status test docs \
	 revision migrate rollback current history

COMPOSE = docker compose
SERVICE = nagrik-ai
ALEMBIC = alembic
# Compose exposes PostgreSQL on localhost for commands run from the host.
MIGRATION_ENV = POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=5433
PORT = 5000
BASE_URL = http://localhost:$(PORT)

# Build the local image and start in the background
build:
	$(COMPOSE) up -d --build

# Start the application and restart it when source files change.
up:
	$(MAKE) dev

# Start file watching and follow application logs in the same terminal.
dev:
	@set -e; \
	trap 'kill 0' INT TERM EXIT; \
	$(COMPOSE) up -d $(SERVICE); \
	$(COMPOSE) watch --no-up $(SERVICE) & \
	$(COMPOSE) logs --follow $(SERVICE)

# Start the application with Docker Compose file watching enabled.
watch:
	$(COMPOSE) watch $(SERVICE)

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

# Create a migration from changes to SQLAlchemy models.
revision:
	$(MIGRATION_ENV) $(ALEMBIC) revision --autogenerate -m "$(message)"

# Apply all pending migrations.
migrate:
	$(MIGRATION_ENV) $(ALEMBIC) upgrade head

# Roll back the latest migration.
rollback:
	$(MIGRATION_ENV) $(ALEMBIC) downgrade -1

# Show the currently applied migration.
current:
	$(MIGRATION_ENV) $(ALEMBIC) current

# Show the migration history.
history:
	$(MIGRATION_ENV) $(ALEMBIC) history