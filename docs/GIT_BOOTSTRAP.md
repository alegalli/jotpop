# Git bootstrap for JotPop

Your error:

```bash
fatal: not a git repository (or any of the parent directories): .git
```

means the folder works as an app, but it has not been initialized as a Git repository yet.

## 1. Create the local checkpoint

From the project root:

```bash
cd ~/Desktop/jotpop
./scripts/init_git_checkpoint.sh
```

If the script asks for Git identity:

```bash
git config --global user.name "Alessandro Galli"
git config --global user.email "YOUR_EMAIL@example.com"
./scripts/init_git_checkpoint.sh
```

## 2. Push to GitHub

### Faster with GitHub CLI

```bash
gh repo create jotpop --private --source=. --remote=origin --push
git push --tags
```

### Without GitHub CLI

1. Create an empty private repo on GitHub named `jotpop`.
2. Do not add README, .gitignore, or license from GitHub.
3. Run:

```bash
git remote add origin https://github.com/YOUR_USERNAME/jotpop.git
git push -u origin main --tags
```

## 3. Do not commit secrets

The patch includes `.gitignore` so these stay local:

```text
.env
.env.*.local
node_modules/
frontend/dist/
```

Never commit real production passwords or JWT secrets.
