.PHONY: all build test release

SHELL := /bin/bash

all: build test

build:
	rm -rf dist
	uv build

test:
	.venv/bin/python3 -m pytest

release:
	@if [[ -n "$$(git status --porcelain)" ]]; then \
		echo "Working tree is dirty. Commit or stash changes before release."; \
		exit 1; \
	fi; \
	read -p "Release version (e.g., 0.1.2): " VERSION; \
	if [[ -z "$$VERSION" ]]; then \
		echo "Version is required."; \
		exit 1; \
	fi; \
	python3 - <<'PY' "$$VERSION"; \
import re\n\
import sys\n\
version = sys.argv[1]\n\
def replace(path, pattern, repl):\n\
    data = open(path, 'r', encoding='utf-8').read()\n\
    new_data, count = re.subn(pattern, repl, data, count=1)\n\
    if count == 0:\n\
        raise SystemExit(f\"{path}: version string not found\")\n\
    open(path, 'w', encoding='utf-8').write(new_data)\n\
\n\
replace('pyproject.toml', r'version\\s*=\\s*\"[^\"]+\"', f'version = \"{version}\"')\n\
replace('src/raggedy/__init__.py', r'__version__\\s*=\\s*\"[^\"]+\"', f'__version__ = \"{version}\"')\n\
PY
	@git add pyproject.toml src/raggedy/__init__.py
	@git commit -m "Release v$$VERSION"
	@git tag v$$VERSION
	@rm -rf dist
	@uv build
	@bash -lc 'source .env && op run -- uv publish'
	@git push
	@git push --tags
