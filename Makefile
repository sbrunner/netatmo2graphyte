PHONY: build
build:
	docker build --tag=sbrunner/netatmo2graphyte .

PHONY: push
push: build
	docker push sbrunner/netatmo2graphyte
