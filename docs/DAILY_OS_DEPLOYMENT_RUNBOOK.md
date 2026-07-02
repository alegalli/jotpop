# JotPop Step 40 — Deploy Daily OS Runbook

This runbook deploys the Daily OS expansion after Step 39 local QA passes.

## Stack

- Database: Neon Postgres
- Backend: Render Free Web Service
- Frontend: Vercel Hobby

## Release rule

Deploy only after local checks pass:

- Docker local app starts.
- `/health` returns `0.32.0` before applying Step 40 or `0.33.0` after applying Step 40.
- Dev → Run Daily OS QA returns `0 failures`.
- Manual checks pass for `/doittoday`, `/plan`, `/minday`, `/done`, Feed, Forge, Evolution.

## Apply Step 40 locally

```bash
cd ~/Desktop/jotpop
docker compose down

cd ~/Downloads
unzip -o jotpop_step40_deploy_daily_os_patch.zip

cd ~/Desktop/jotpop
cp ~/Downloads/jotpop_step40_deploy_daily_os_patch/backend/app/core/config.py backend/app/core/config.py
cp ~/Downloads/jotpop_step40_deploy_daily_os_patch/scripts/daily_os_post_deploy_check.sh scripts/daily_os_post_deploy_check.sh
mkdir -p docs
cp ~/Downloads/jotpop_step40_deploy_daily_os_patch/docs/DAILY_OS_DEPLOYMENT_RUNBOOK.md docs/DAILY_OS_DEPLOYMENT_RUNBOOK.md
cp ~/Downloads/jotpop_step40_deploy_daily_os_patch/docs/DAILY_OS_RELEASE_CHECKLIST.md docs/DAILY_OS_RELEASE_CHECKLIST.md
cp ~/Downloads/jotpop_step40_deploy_daily_os_patch/docs/NEON_MVP_RESET_NOTES.md docs/NEON_MVP_RESET_NOTES.md
chmod +x scripts/daily_os_post_deploy_check.sh
```

## Local final check

```bash
docker compose up --build
curl http://127.0.0.1:8000/health
```

Expected version: `0.33.0`.

Open the local app and run Dev → Run Daily OS QA.

## Commit and push

```bash
cd ~/Desktop/jotpop
git status
git add .
git commit -m "Step 40 deploy Daily OS"
git tag daily-os-live-1
git push
git push --tags
```

## Render backend deploy

Render should auto-deploy after the push. If not:

1. Open Render → `jotpop-api`.
2. Confirm settings:
   - Branch: `main`
   - Root Directory: `backend`
   - Runtime: Docker
   - Instance: Free
   - Dockerfile Path: `Dockerfile`
   - Docker Build Context: `.`
3. Environment variables:
   - `DATABASE_URL=<Neon connection string>`
   - `JWT_SECRET_KEY=<long random value>`
   - `DEV_USER_EMAILS=ale@example.com`
   - `FRONTEND_ALLOWED_ORIGINS=<your Vercel URL, no trailing slash>`
4. Manual Deploy → Deploy latest commit.

Backend health should return version `0.33.0`:

```bash
curl https://YOUR_RENDER_BACKEND_URL/health
```

## Vercel frontend deploy

Vercel should auto-deploy after the push. If not:

1. Open Vercel → JotPop project.
2. Confirm:
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - `VITE_API_BASE_URL=https://YOUR_RENDER_BACKEND_URL` with no trailing slash
3. Redeploy latest commit.

## Post-deploy check

Basic:

```bash
./scripts/daily_os_post_deploy_check.sh \
  https://YOUR_RENDER_BACKEND_URL \
  https://YOUR_VERCEL_FRONTEND_URL
```

Authenticated:

```bash
JOTPOP_TEST_EMAIL=ale@example.com \
JOTPOP_TEST_PASSWORD='YOUR_PASSWORD' \
JOTPOP_TEST_TIMEZONE=Europe/Dublin \
./scripts/daily_os_post_deploy_check.sh \
  https://YOUR_RENDER_BACKEND_URL \
  https://YOUR_VERCEL_FRONTEND_URL
```

## Manual production check

Open the Vercel URL and test:

- Login/register.
- Open Menu.
- `/doittoday` loads and shows automatic Minimum Day tasks.
- `/plan` can add a future task.
- `/minday` can edit THE MINIMUM DAY and shows preview.
- `/done` shows last 7 days.
- Feed still full-screen.
- Forge still works.
- Evolution avatar still appears.
- Dev → Run Daily OS QA returns `0 failures`.

