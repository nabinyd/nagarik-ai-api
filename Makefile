.PHONY: build up down stop restart logs

build:
	docker compose -f docker-compose.staging.yml up -d --build

up:
	docker compose -f docker-compose.staging.yml up

down:
	docker compose -f docker-compose.staging.yml down

stop:
	docker compose -f docker-compose.staging.yml stop

restart:
	docker compose -f docker-compose.staging.yml restart

logs:
	docker compose -f docker-compose.staging.yml logs -f