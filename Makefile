REGISTRY ?= 192.168.1.112:49155
IMAGE     ?= $(REGISTRY)/motiontracker
VERSION   ?= $(shell date +%Y.%-m.%-d)

.PHONY: help build push deploy dev-up dev-down test

help:
	@echo "MotionTracker"
	@echo ""
	@echo "  dev-up    Start local dev (docker-compose)"
	@echo "  dev-down  Stop local dev"
	@echo "  build     Build Docker image (VERSION=$(VERSION))"
	@echo "  push      Push image to Synology registry"
	@echo "  deploy    Build + push"
	@echo "  test      Run tests"

_check-version:
	@echo "$(VERSION)" | grep -qE '^[0-9]{4}\.[0-9]{1,2}\.[0-9]{1,2}$$' || \
		(echo "ERROR: VERSION format must be YYYY.M.D  eg. 2026.3.29" && exit 1)

build: _check-version
	docker buildx build --platform=linux/amd64 \
		-t $(IMAGE):$(VERSION) \
		-t $(IMAGE):latest \
		.

push: _check-version
	docker push $(IMAGE):$(VERSION)
	docker push $(IMAGE):latest

deploy: build push
	@echo ""
	@echo "Pushed $(IMAGE):$(VERSION)"
	@echo "Update kubis-flux: apps/default/motiontracker/deployment.yaml image tag to $(VERSION)"

dev-up:
	cp -n .env.example .env 2>/dev/null || true
	docker compose -f docker-compose.dev.yml up -d

dev-down:
	docker compose -f docker-compose.dev.yml down

test:
	python -m pytest tests/ -v
