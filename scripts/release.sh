#!/bin/bash
set -euo pipefail

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree is dirty. Commit or stash changes before release."
  exit 1
fi

make test

read -p "Release version (e.g., 0.1.2): " VERSION
if [[ -z "${VERSION}" ]]; then
  echo "Version is required."
  exit 1
fi

python3 - "${VERSION}" <<'PY'
import re
import sys

version = sys.argv[1]

def replace(path, pattern, repl):
    data = open(path, "r", encoding="utf-8").read()
    new_data, count = re.subn(pattern, repl, data, count=1)
    if count == 0:
        raise SystemExit(f"{path}: version string not found")
    open(path, "w", encoding="utf-8").write(new_data)

replace("pyproject.toml", r'version\\s*=\\s*\"[^\"]+\"', f'version = "{version}"')
replace("src/raggedy/__init__.py", r'__version__\\s*=\\s*\"[^\"]+\"', f'__version__ = "{version}"')
PY

git add pyproject.toml src/raggedy/__init__.py
git commit -m "Release v${VERSION}"
git tag "v${VERSION}"

rm -rf dist
uv build
bash -lc 'source .env && op run -- uv publish'

git push
git push --tags
