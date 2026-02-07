.PHONY: all build test release

SHELL := /bin/bash

all: build test

build:
	rm -rf dist
	uv build

test:
	.venv/bin/python3 -m pytest

release:
	@bash scripts/release.sh
