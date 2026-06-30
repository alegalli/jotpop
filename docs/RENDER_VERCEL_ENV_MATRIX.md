# Render / Vercel environment matrix

## Render backend

| Key | Value |
| --- | --- |
| DATABASE_URL | from Render Postgres `jotpop-db` connection string |
| JWT_SECRET_KEY | generated secret |
| JWT_ALGORITHM | `HS256` |
| DEV_USER_EMAILS | `ale@example.com` |
| FRONTEND_ALLOWED_ORIGINS | Vercel frontend URL, no trailing slash |

## Vercel frontend

| Key | Value |
| --- | --- |
| VITE_API_BASE_URL | Render backend URL, no trailing slash |

## Common mistakes

```text
Wrong: VITE_API_BASE_URL=http://127.0.0.1:8000
Right: VITE_API_BASE_URL=https://your-api.onrender.com
```

```text
Wrong: FRONTEND_ALLOWED_ORIGINS empty after frontend is deployed
Right: FRONTEND_ALLOWED_ORIGINS=https://your-app.vercel.app
```

```text
Wrong: using trailing slashes everywhere
Right: use URLs without trailing slash in env vars
```
