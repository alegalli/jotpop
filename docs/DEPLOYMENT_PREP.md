# JotPop Deployment Prep

This step prepares the app for deployment. It does not force one hosting provider.

## Important production changes in Step 32

Step 32 adds:

- `VITE_API_BASE_URL` support in the frontend.
- `FRONTEND_ALLOWED_ORIGINS` support in the backend CORS settings.
- `.env.production.example`.
- `frontend/.env.production.example`.
- `docker-compose.demo.yml` for controlled demo-style deployments.
- Future backlog and release checklist docs.

## Local dev still works

The frontend falls back to:

```text
http://127.0.0.1:8000
```

So local Docker usage does not require a frontend env file.

## Backend environment variables

Required:

```text
DATABASE_URL
JWT_SECRET_KEY
```

Strongly recommended for deployment:

```text
FRONTEND_ALLOWED_ORIGINS=https://your-frontend-domain.example.com
DEV_USER_EMAILS=ale@example.com
```

## Frontend environment variables

Required for deployment:

```text
VITE_API_BASE_URL=https://your-backend-domain.example.com
```

## Smoke test after deployment

Backend:

```bash
curl https://your-backend-domain.example.com/health
```

Expected:

```json
{"status":"ok","service":"jotpop-api","version":"0.25.0"}
```

Frontend:

- Open the deployed frontend URL.
- Sign in.
- Run the Dev smoke check from the dev account.

## Release guidance

For tomorrow's release, keep it private/demo-only:

- one developer account
- one or two trusted test users
- no public marketing yet
- no sensitive/private life data from external users yet

Before public users, add production auth, migrations, rate limits, privacy/data deletion, and real monitoring.
