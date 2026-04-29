# Perazzo API

Backend API for the Perazzo POS/commerce system. It powers store management, authentication, products, categories, customers, orders, carts, delivery methods, payment methods, cash register entries, couriers, and public catalog data.

The API is built with FastAPI and PostgreSQL, and is designed to run locally with Docker Compose.

## Tech Stack

- Python 3.12
- FastAPI
- Uvicorn
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic and pydantic-settings
- python-jose for JWT handling
- passlib and bcrypt for password hashing
- python-slugify
- Docker and Docker Compose

## Project Structure

- `app/main.py`: FastAPI application entry point.
- `app/api/v1`: API route registration and routers.
- `app/core`: configuration, database setup, dependencies, and security helpers.
- `app/domain/models`: SQLAlchemy models.
- `app/schemas`: Pydantic request and response schemas.
- `app/services`: business logic.
- `app/util`: shared utility functions.
- `migrations`: Alembic migration environment and migration files.
- `docker-compose.yml`: local API and PostgreSQL setup.
- `Dockerfile`: API container image.

## Environment Variables

Local Docker variables are stored in `.env.docker`.

Required variables:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/perazzo_db
SECRET_KEY=local-dev-secret-key
EMAIL_SECRET_KEY=local-dev-email-secret-key
RESET_SECRET_KEY=local-dev-reset-secret-key
FRONTEND_URL=http://localhost:3000
BACKEND_CORS_ORIGINS=http://localhost:3000,https://perazzo-manager.vercel.app
```

For running the API outside Docker, `.env.local` uses the host database port:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5433/perazzo_db
SECRET_KEY=local-dev-secret-key
EMAIL_SECRET_KEY=local-dev-email-secret-key
RESET_SECRET_KEY=local-dev-reset-secret-key
FRONTEND_URL=http://localhost:3000
BACKEND_CORS_ORIGINS=http://localhost:3000,https://perazzo-manager.vercel.app
```

Use stronger secrets in production.

Optional SMTP variables for account verification and password reset emails:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user
SMTP_PASSWORD=password
SMTP_FROM_EMAIL=no-reply@example.com
SMTP_FROM_NAME=Perazzo Manager
SMTP_USE_TLS=true
```

When SMTP is not configured in local development, verification and password reset links are written to the API logs and are never returned in the HTTP response. In production, set `APP_DEBUG=false`, configure `BACKEND_CORS_ORIGINS` with the exact frontend domains, and keep SMTP secrets only in the deployment environment.

Production frontend settings for Render:

```env
FRONTEND_URL=https://perazzo-manager.vercel.app
BACKEND_CORS_ORIGINS=https://perazzo-manager.vercel.app
```

## Install and Run with Docker

Prerequisites:

- Docker Desktop installed and running.
- Port `5433` available for PostgreSQL.
- Port `8001` available for the API.

Start the database and API:

```powershell
docker compose up --build -d
```

Follow API logs:

```powershell
docker compose logs -f api
```

The API container waits for PostgreSQL, runs Alembic migrations, and then starts Uvicorn.

Check the health endpoint:

```powershell
curl http://localhost:8001/health
```

Expected response:

```json
{"status":"ok"}
```

## Local URLs

- API: `http://localhost:8001`
- Healthcheck: `http://localhost:8001/health`
- API v1 prefix: `http://localhost:8001/api/v1`
- PostgreSQL: `localhost:5433`

## Useful Commands

Stop the containers:

```powershell
docker compose down
```

Stop the containers and remove the local database volume:

```powershell
docker compose down -v
```

Run migrations manually inside the API container:

```powershell
docker compose exec api alembic upgrade head
```

Open a shell inside the API container:

```powershell
docker compose exec api sh
```

## Frontend Integration

When running `perazzo-manager` locally against this Docker setup, configure the frontend API URL as:

```env
NEXT_PUBLIC_PERAZZO_API_URL=http://localhost:8001/api/v1
```
