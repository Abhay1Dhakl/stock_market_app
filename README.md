# Stock Market Application

Submission-ready take-home assignment for crawling NEPSE-related news and market data, automatically categorizing news against tracked companies, computing behavior-analysis outputs, and exposing the workflow through role-based backend and frontend screens.

## What Is Implemented

- FastAPI backend with JWT authentication and RBAC for `admin`, `analyst`, and `viewer`
- PostgreSQL schema for companies, crawl runs, news, tags, daily prices, floorsheet rows, and analysis snapshots
- Live news crawling from `sharesansar.com` and `merolagani.com`
- Live daily price and floorsheet ingestion from `sharesansar.com`
- Rule-based multi-label news categorization with confidence scores
- Manual analyst/admin recategorization with correction history
- Derived behavior-analysis snapshots:
  - VWAP
  - price and volume change percentages
  - pressure indicator
  - volume anomaly flag
  - news count and sentiment score
  - next-day price/volume movement references
  - top broker net-position summary
- Celery worker + beat wiring for scheduled crawl support
- Next.js frontend pages for:
  - login
  - dashboard
  - company detail
  - review queue
  - admin console

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Alembic, Celery, Redis, PostgreSQL
- Frontend: Next.js 15, React 19, TypeScript
- Crawling/parsing: `httpx`, `beautifulsoup4`, `lxml`
- Categorization: rule-based matcher with alias/symbol confidence scoring

## Seeded Company Universe

The app auto-seeds six NEPSE companies on crawl/analysis execution:

- `NABIL`
- `NTC`
- `SHIVM`
- `UPPER`
- `SICL`
- `CHCL`

## Local Run

1. Copy the environment file:

```bash
cp .env.example .env
```

2. Start the full stack:

```bash
docker compose up --build
```

3. Run the database migration:

```bash
docker compose exec backend alembic upgrade head
```

4. Open the app:

- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`

## Default Admin

Bootstrapped local admin credentials:

- Email: `admin@example.com`
- Password: `admin123`

These can be overridden with `BOOTSTRAP_ADMIN_*` values in `.env`.

## Recommended Demo Flow

1. Sign in from `/login`
2. Open `/admin`
3. Trigger a `full` crawl with `execute inline now` enabled
4. Open `/dashboard`
5. Drill into a company detail page
6. Open `/review` and manually correct any low-confidence article

## Useful Commands

Start only the worker locally:

```bash
make worker
```

Start only beat locally:

```bash
make beat
```

Run backend tests:

```bash
python3 -m pytest backend/tests -q
```

## Verification Completed

Verified on August 4, 2026:

- Backend tests: `16 passed`
- Backend compile pass: `python3 -m compileall backend/app`
- Frontend production build: `docker compose run --rm --no-deps frontend npm run build`

## Notes On Scope

- Categorization is intentionally rule-based rather than ML-heavy to keep the end-to-end product working and reviewable within the assignment timebox.
- The frontend is focused on a functional demo workflow rather than chart-heavy polish.
- Market-data crawling currently uses ShareSansar as the live source for OHLCV and floorsheet sampling.
