.PHONY: all build test release

SHELL := /bin/bash
.ONESHELL:

all: build test

build:
	rm -rf dist
	uv build

test:
	.venv/bin/python3 -m pytest

release:
	if [[ -n "$$(git status --porcelain)" ]]; then
		echo "Working tree is dirty. Commit or stash changes before release."
		exit 1
	fi
	$(MAKE) test
	bash scripts/release.sh
