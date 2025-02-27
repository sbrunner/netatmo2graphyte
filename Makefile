GITHUB_REPOSITORY ?= sbrunner/netatmo2graphite
export DOCKER_BUILDKIT = 1

.PHONY: build
build: checks
	docker build --tag=$(GITHUB_REPOSITORY) .

PHONY: push
push: build
	docker push $(GITHUB_REPOSITORY)

.PHONY: build-checker
build-checker:
	docker build --target=checker --tag=$(GITHUB_REPOSITORY)-checker .

.PHONY: checks
checks: prospector

.PHONY: prospector
prospector: build-checker
	docker run --rm --volume=${PWD}:/app $(GITHUB_REPOSITORY)-checker prospector -X --output=pylint netatmo2graphite.py
