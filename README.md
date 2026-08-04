# Stock Market Application

This repository contains the take-home assignment for a stock market application focused on:

- crawling market news from multiple portals
- categorizing each article against a company watchlist
- computing behavior-analysis outputs from price and floorsheet data
- exposing everything through a role-based dashboard

## Current Status

Phase 1 scaffold is in place:

- FastAPI backend shell
- Next.js frontend shell
- Docker Compose baseline for backend, frontend, PostgreSQL, and Redis
- Folder structure aligned with the assignment brief

## Planned Stack

- Backend: FastAPI, SQLAlchemy, Alembic, Celery, Redis, PostgreSQL
- Frontend: Next.js, React, TypeScript
- Categorization: rule-based multi-label baseline with confidence scoring

## Next Step

Phase 2 will define the database schema and core models for:

- users and roles
- companies and watchlist metadata
- news articles and categorizations
- daily prices and floorsheet transactions
- crawl runs and computed analysis snapshots

## Default Admin

When the backend starts with a reachable database, it can bootstrap a default admin user for local/demo use:

- email: `admin@example.com`
- password: `admin123`

Override these with the `BOOTSTRAP_ADMIN_*` environment variables.
