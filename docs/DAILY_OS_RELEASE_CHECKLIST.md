# Daily OS Release Checklist

## Pre-deploy local

- [ ] Docker starts locally.
- [ ] `/health` returns `0.33.0` after Step 40.
- [ ] Login works.
- [ ] Side menu opens/closes smoothly.
- [ ] `/doittoday` works.
- [ ] `/plan` works.
- [ ] `/minday` works.
- [ ] `/done` works.
- [ ] Dev → Run Daily OS QA returns `0 failures`.
- [ ] Feed still works.
- [ ] Forge still works.
- [ ] Evolution still works.

## Git

- [ ] Step 40 committed.
- [ ] `daily-os-live-1` tag created.
- [ ] Main pushed to GitHub.
- [ ] Tags pushed to GitHub.

## Render

- [ ] Backend redeployed from latest commit.
- [ ] Root Directory is `backend`.
- [ ] `DATABASE_URL` points to Neon.
- [ ] `FRONTEND_ALLOWED_ORIGINS` contains Vercel URL.
- [ ] `/health` returns `0.33.0`.

## Vercel

- [ ] Frontend redeployed from latest commit.
- [ ] Root Directory is `frontend`.
- [ ] `VITE_API_BASE_URL` points to Render backend.
- [ ] Production URL opens.

## Post-deploy

- [ ] `daily_os_post_deploy_check.sh` passes basic checks.
- [ ] Authenticated Daily OS checks pass.
- [ ] Manual browser test passes.

