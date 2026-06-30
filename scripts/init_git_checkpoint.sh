#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d .git ]; then
  echo "Initializing git repository..."
  git init
  git branch -M main
else
  echo "Git repository already exists."
fi

if ! git config user.email >/dev/null; then
  echo "Git user.email is not configured."
  echo "Run: git config --global user.email \"you@example.com\""
  exit 1
fi

if ! git config user.name >/dev/null; then
  echo "Git user.name is not configured."
  echo "Run: git config --global user.name \"Your Name\""
  exit 1
fi

git add .

if git diff --cached --quiet; then
  echo "Nothing new to commit."
else
  git commit -m "MVP release candidate deployment setup"
fi

if git rev-parse mvp-rc-1 >/dev/null 2>&1; then
  echo "Tag mvp-rc-1 already exists."
else
  git tag mvp-rc-1
fi

echo ""
echo "Git checkpoint ready."
echo "Next: create/push a GitHub repo."
echo "If you have GitHub CLI:"
echo "  gh repo create jotpop --private --source=. --remote=origin --push"
echo "Otherwise create an empty GitHub repo in the browser, then run:"
echo "  git remote add origin https://github.com/YOUR_USERNAME/jotpop.git"
echo "  git push -u origin main --tags"
