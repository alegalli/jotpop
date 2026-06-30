# Step 33 release notes

## Purpose

Prepare JotPop for the first managed demo deployment.

## Changes

```text
- Add Git bootstrap script.
- Add post-deploy smoke test script.
- Add .gitignore to protect secrets and generated files.
- Add Render Blueprint template.
- Add Vercel SPA fallback config.
- Update backend Dockerfile to use Render's PORT variable.
- Normalize postgres:// database URLs for SQLAlchemy compatibility.
- Bump backend version to 0.26.0.
```

## Not included

```text
- No Feed feature changes.
- No Forge feature changes.
- No Evolution redesign.
- No new card content.
```

This is a release/deployment step only.
