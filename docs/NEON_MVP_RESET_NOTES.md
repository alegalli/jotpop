# Neon MVP Reset Notes

The current JotPop deployment is still MVP/destructive-friendly. The only real user is Alessandro, so if Daily OS schema/data becomes messy, resetting Neon is acceptable.

## Preferred first move

Do not reset unless needed. The backend creates missing tables automatically.

## Reset only if

- Production deploy starts but Daily OS tables are inconsistent.
- You changed schema locally and production has incompatible old tables.
- You deliberately want a clean demo state.

## Safer reset strategy

In Neon:

1. Create a new branch/database or reset the current project from the dashboard if you are comfortable losing data.
2. Copy the new connection string.
3. Update Render `DATABASE_URL`.
4. Redeploy Render.
5. Register/login again in the app.
6. Run Daily OS QA.

## Warning

Once real users exist, do not reset production data. Add Alembic/proper migrations before real public usage.

