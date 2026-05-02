# Portexa Backend

FastAPI + PostgreSQL backend for login/signup with account lockout.

## Setup
1. Copy `.env.example` to `.env` and edit values.
2. Create your PostgreSQL database and update `DATABASE_URL`.
3. Install dependencies: `pip install -r requirements.txt`
4. Run migrations: `alembic upgrade head`
5. Run: `uvicorn app.main:app --reload`

## Convenience (Windows)
- Run migrations: `./scripts.ps1 -Migrate`
- Run server: `./scripts.ps1 -Run`

## Routes
- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/health`

## Notes
- Login is locked for 30 minutes after 3 failed attempts (configurable in `.env`).
- Uses auto table creation on startup. Use Alembic for production migrations.
