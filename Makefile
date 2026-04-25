.DEFAULT_GOAL := help
SHELL := /bin/bash

DB_NAME ?= odooforge

.PHONY: help up down restart logs ps shell psql init-db install-helpdesk update-helpdesk reset clean

help:
	@echo "OdooForge local stack"
	@echo ""
	@echo "  make up                  Start the stack in the background"
	@echo "  make down                Stop the stack"
	@echo "  make restart             Restart Odoo only"
	@echo "  make logs                Tail Odoo logs"
	@echo "  make ps                  Show container status"
	@echo "  make shell               Open a bash shell in the Odoo container"
	@echo "  make psql                Open psql against the Odoo database"
	@echo "  make init-db             Create the Odoo database and install base + helpdesk_mgmt"
	@echo "  make install-helpdesk    Install helpdesk_mgmt into an existing database"
	@echo "  make update-helpdesk     Update helpdesk_mgmt module code"
	@echo "  make reset               Drop the Odoo database and re-init"
	@echo "  make clean               Stop the stack and remove all volumes (destroys data)"

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart odoo

logs:
	docker compose logs -f --tail=200 odoo

ps:
	docker compose ps

shell:
	docker compose exec odoo bash

psql:
	docker compose exec db psql -U odoo -d $(DB_NAME)

init-db:
	docker compose exec odoo odoo -c /etc/odoo/odoo.conf -d $(DB_NAME) -i base,helpdesk_mgmt --stop-after-init --without-demo=False

install-helpdesk:
	docker compose exec odoo odoo -c /etc/odoo/odoo.conf -d $(DB_NAME) -i helpdesk_mgmt --stop-after-init

update-helpdesk:
	docker compose exec odoo odoo -c /etc/odoo/odoo.conf -d $(DB_NAME) -u helpdesk_mgmt --stop-after-init

reset:
	docker compose exec db dropdb -U odoo --if-exists $(DB_NAME)
	$(MAKE) init-db

clean:
	docker compose down -v
