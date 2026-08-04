# Stock Market Application

Submission-oriented full-stack assignment for crawling NEPSE-related news and market data, automatically tagging news against a tracked company watchlist, computing behavior-analysis outputs, and exposing the workflow through role-aware backend and frontend screens.

## Priority And Scope

This implementation intentionally prioritizes:

- backend architecture that is modular and production-shaped
- server-side RBAC and API correctness
- a working end-to-end crawl -> categorize -> analyze -> review flow
- a functional Next.js dashboard with company detail, review, and admin operations

Because the assignment is time-boxed, the categorization pipeline now supports an LLM-first path using Gemini 2.5 Flash with a deterministic rule-based fallback. That keeps the submission stronger on the AI/ML side without making local execution brittle when an external API key is unavailable.

## What Is Implemented

- FastAPI backend with JWT authentication and server-side RBAC for `admin`, `analyst`, and `viewer`
- PostgreSQL schema separating:
  - raw crawled news
  - company watchlist and market data
  - news/company tags and manual corrections
  - computed daily analysis snapshots
- Live news crawling from:
  - `merolagani.com`
  - `sharesansar.com`
- Live market-data crawling from `sharesansar.com` for:
  - daily OHLCV
  - turnover
  - floorsheet sampling when the live source returns rows
- Automatic multi-label company tagging with confidence scores
- Gemini 2.5 Flash based categorization via structured JSON output when configured
- Deterministic rule-based fallback categorization when Gemini is unavailable or disabled
- Manual analyst/admin recategorization with correction history
- Derived behavior-analysis snapshots:
  - VWAP
  - daily price change percentage
  - daily volume change percentage
  - buy/sell pressure indicator
  - volume anomaly flag
  - tagged news count
  - news sentiment score
  - next-day price and volume movement references
  - top broker net-position summary when floorsheet rows are available
- Celery worker + beat scheduling for crawl execution
- Next.js frontend pages for:
  - login
  - cross-company dashboard
  - company detail board
  - manual review desk
  - operations/admin console

## Data Sources

### News Portals

- `https://merolagani.com/NewsList.aspx`
- `https://www.sharesansar.com/news-page`

### Market Data

- `https://www.sharesansar.com/company/{symbol}`
- ShareSansar price history endpoint
- ShareSansar floorsheet endpoint

## Seeded Watchlist

The current watchlist is seeded from [data/seed/companies.json](data/seed/companies.json) and contains six companies across multiple sectors:

- `NABIL`
- `NTC`
- `SHIVM`
- `UPPER`
- `SICL`
- `CHCL`

The assignment requested 5-10 companies. This repository currently uses 6 companies, which stays inside that range.

## Categorization Approach

The categorization engine now supports two paths:

1. **Gemini 2.5 Flash path**
   - send the article headline, body, and tracked company watchlist to Gemini
   - request structured JSON output through the Gemini Interactions API
   - persist one or more company tags with model-provided confidence scores and short match summaries
   - if the Gemini request fails at runtime, fall back to the rule-based matcher for that article

2. **Rule-based fallback path**
   - normalize article title and body text
   - build a term set from each tracked company's symbol, name, and aliases
   - count exact symbol/alias hits in the title and body
   - compute a confidence score from:
     - alias hit count
     - symbol hit count
     - title hit count
     - distinct matched terms
     - article body length

Key files:

- Gemini matcher: [`backend/app/categorization/gemini_matcher.py`](backend/app/categorization/gemini_matcher.py)
- matcher: [`backend/app/categorization/entity_matcher.py`](backend/app/categorization/entity_matcher.py)
- confidence scoring: [`backend/app/categorization/confidence.py`](backend/app/categorization/confidence.py)
- orchestration: [`backend/app/services/categorization_service.py`](backend/app/services/categorization_service.py)

### Why This Approach

- Gemini 2.5 Flash gives a stronger AI-assisted categorization story for the assignment and interview discussion.
- Structured JSON output keeps the model response machine-readable and easy to validate.
- The fallback matcher preserves local reliability and keeps the review queue flowing even if the LLM path is unavailable.
- Manual correction still remains the source of truth for bad or ambiguous tags.

### Trade-Offs

- The Gemini path depends on an external API key and introduces network latency and cost.
- The fallback matcher still depends heavily on alias quality in the watchlist.
- Neither path is a supervised finance-specific classifier, so manual review is still important for ambiguous articles.

## Behavior Analysis Outputs

Daily analysis snapshots are materialized and stored rather than recomputed on every request.

The current analysis pipeline computes:

- close price and VWAP
- daily price and volume change percentages
- pressure indicator from price and volume movement
- anomaly thresholds using a rolling average multiplied by `1.8`
- anomaly flags when daily volume crosses that threshold
- same-day tagged news count and sentiment score
- next-day price and volume change references
- net broker positions from floorsheet rows when present

Key files:

- pipeline: [`backend/app/services/analysis_service.py`](backend/app/services/analysis_service.py)
- pressure: [`backend/app/analysis/pressure.py`](backend/app/analysis/pressure.py)
- VWAP helper: [`backend/app/analysis/price_metrics.py`](backend/app/analysis/price_metrics.py)
- broker aggregation: [`backend/app/analysis/broker_analysis.py`](backend/app/analysis/broker_analysis.py)

The written findings summary required by the assignment is in [docs/findings-summary.md](docs/findings-summary.md).

## Architecture Overview

### Backend

- Framework: FastAPI
- DB access: SQLAlchemy
- Migrations: Alembic
- Queue/scheduler: Celery + Redis
- DB: PostgreSQL

### Frontend

- Framework: Next.js 15 + React 19 + TypeScript
- Auth model: browser-stored JWT demo session
- Main surfaces:
  - watchlist dashboard
  - company board with chart and broker analysis
  - manual review desk
  - operations/admin console

### System Flow

1. Crawl news and market data into PostgreSQL.
2. Categorize articles against the watchlist.
3. Compute analysis snapshots from stored prices, tags, and floorsheet rows.
4. Expose those results via FastAPI endpoints.
5. Read those endpoints from the Next.js dashboard.

For a guided code walkthrough, see [docs/codebase-guide.md](docs/codebase-guide.md).

## API Surface

Implemented primary endpoints include:

- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/companies`
- `GET /api/companies/:id`
- `GET /api/companies/:id/prices?range=30d`
- `GET /api/companies/:id/floorsheet?date=`
- `GET /api/companies/:id/behavior-summary`
- `GET /api/companies/:id/news-price-correlation`
- `GET /api/news?company_id=`
- `GET /api/news/review-queue`
- `POST /api/news/:id/recategorize`
- `POST /api/admin/crawl-runs`
- `GET /api/admin/crawl-runs`
- `GET /api/admin/crawl-runs/:id`
- `GET /api/admin/users`
- `POST /api/admin/users`

OpenAPI is available at:

- `http://localhost:8000/docs`

## Local Run

1. Copy the environment file:

```bash
cp .env.example .env
```

If you want LLM-based categorization, set `GEMINI_API_KEY` in `.env`. The default provider is `gemini`, and the service falls back to the rule-based matcher if the key is missing or the API request fails.

2. Start the full stack:

```bash
docker compose up --build
```

3. If you want to apply migrations manually, run:

```bash
docker compose exec backend alembic upgrade head
```

Note: the backend also attempts to run migrations on startup.

4. Open the app:

- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`

## Default Admin Credentials

- Email: `admin@example.com`
- Password: `admin123`

These can be overridden with `BOOTSTRAP_ADMIN_*` values in `.env`.

## Recommended Demo Flow

1. Sign in from `/login`.
2. Open `/admin`.
3. Trigger a `full` crawl with inline execution enabled.
4. Open `/dashboard`.
5. Open any company board from the watchlist.
6. Inspect:
   - 30 day trend chart
   - recent tagged news
   - behavior summary
   - buyer/seller analysis
7. Open `/review` and manually correct a low-confidence article.

## Verification Completed

Verified on **August 4, 2026**:

- backend tests: `18 passed`
- frontend production build: `docker compose run --rm --no-deps frontend npm run build`
- live crawl verification:
  - `6` companies seeded
  - `180` daily price rows created
  - `24` news articles stored
  - `1` auto-tagged article
  - `23` review-queue candidates

## Time-Boxed Assumptions And Shortcuts

- Categorization is rule-based rather than embedding-based or LLM-based.
- The tracked watchlist is seeded from JSON rather than fully admin-managed through CRUD screens.
- Analyst export/report download endpoints are not implemented yet.
- Broker analysis depends on live floorsheet availability from the source site. The code path exists, tests cover it, and the UI supports it, but some live runs may return zero floorsheet rows.
- Local `docker compose` execution is the primary delivery path. No public deployment URL is included in this repository.

## Useful Commands

Run backend tests:

```bash
python3 -m pytest backend/tests -q
```

Run a frontend production build:

```bash
docker compose run --rm --no-deps frontend npm run build
```

Start only the worker locally:

```bash
make worker
```

Start only beat locally:

```bash
make beat
```

## Additional Docs

- findings summary: [docs/findings-summary.md](docs/findings-summary.md)
- codebase guide: [docs/codebase-guide.md](docs/codebase-guide.md)
