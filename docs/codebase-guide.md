# Codebase Guide

This project becomes easy to understand once you read it as **one pipeline** instead of as separate frontend and backend folders.

## The Pipeline

1. **Collect data**
   - crawl news articles from supported portals
   - crawl market data for the tracked watchlist

2. **Store data**
   - news goes into `news_articles`
   - market data goes into `daily_prices` and `floorsheet_transactions`
   - crawl metadata goes into `crawl_runs`

3. **Categorize news**
   - match article text against the company watchlist
   - store one or more tags per article with a confidence score
   - send weak or empty matches into the review queue

4. **Compute analysis**
   - derive VWAP, pressure, anomalies, news counts, and correlation fields
   - store those outputs in `company_analysis_snapshots`

5. **Expose APIs**
   - prices, floorsheet, news, analysis, review queue, report export, and admin operations

6. **Render the UI**
   - dashboard for cross-company monitoring
   - company detail board for deeper analysis
   - review desk for human correction
   - admin console for crawl and user operations

## Best Reading Order

### 1. Start With The Entry Points

- backend app wiring: [`backend/app/main.py`](../backend/app/main.py)
- frontend shell and routes:
  - [`frontend/app/page.tsx`](../frontend/app/page.tsx)
  - [`frontend/app/dashboard/page.tsx`](../frontend/app/dashboard/page.tsx)
  - [`frontend/app/companies/[id]/page.tsx`](../frontend/app/companies/[id]/page.tsx)
  - [`frontend/app/review/page.tsx`](../frontend/app/review/page.tsx)
  - [`frontend/app/admin/page.tsx`](../frontend/app/admin/page.tsx)

### 2. Read The Backend By Responsibility

#### `models/`

These files define what the system stores:

- companies: [`backend/app/models/company.py`](../backend/app/models/company.py)
- market data: [`backend/app/models/market_data.py`](../backend/app/models/market_data.py)
- news and corrections: [`backend/app/models/news.py`](../backend/app/models/news.py)
- analysis snapshots: [`backend/app/models/analysis_snapshot.py`](../backend/app/models/analysis_snapshot.py)
- crawl tracking: [`backend/app/models/crawl_run.py`](../backend/app/models/crawl_run.py)
- users and roles:
  - [`backend/app/models/user.py`](../backend/app/models/user.py)
  - [`backend/app/models/role.py`](../backend/app/models/role.py)

#### `crawlers/`

These files talk to external sites:

- crawler base: [`backend/app/crawlers/base.py`](../backend/app/crawlers/base.py)
- MeroLagani news: [`backend/app/crawlers/merolagani.py`](../backend/app/crawlers/merolagani.py)
- ShareSansar news: [`backend/app/crawlers/sharesansar.py`](../backend/app/crawlers/sharesansar.py)
- ShareSansar market data: [`backend/app/crawlers/market_data.py`](../backend/app/crawlers/market_data.py)

#### `services/`

These files hold the main business logic:

- crawl orchestration: [`backend/app/services/crawl_service.py`](../backend/app/services/crawl_service.py)
- categorization: [`backend/app/services/categorization_service.py`](../backend/app/services/categorization_service.py)
- analysis pipeline: [`backend/app/services/analysis_service.py`](../backend/app/services/analysis_service.py)
- auth helper: [`backend/app/services/auth_service.py`](../backend/app/services/auth_service.py)
- startup bootstrap: [`backend/app/services/bootstrap.py`](../backend/app/services/bootstrap.py)

#### `api/`

These files expose the services over HTTP:

- auth: [`backend/app/api/auth.py`](../backend/app/api/auth.py)
- companies and market data: [`backend/app/api/companies.py`](../backend/app/api/companies.py)
- news and review queue: [`backend/app/api/news.py`](../backend/app/api/news.py)
- behavior analysis: [`backend/app/api/analysis.py`](../backend/app/api/analysis.py)
- admin flows: [`backend/app/api/admin.py`](../backend/app/api/admin.py)
- report export: [`backend/app/api/reports.py`](../backend/app/api/reports.py)

### 3. Read Cross-Cutting Backend Files

- RBAC: [`backend/app/core/permissions.py`](../backend/app/core/permissions.py)
- JWT/security: [`backend/app/core/security.py`](../backend/app/core/security.py)
- config/envs: [`backend/app/core/config.py`](../backend/app/core/config.py)
- exception handlers: [`backend/app/core/exceptions.py`](../backend/app/core/exceptions.py)
- Celery schedule: [`backend/app/celery_app.py`](../backend/app/celery_app.py)

### 4. Read The Frontend By Screen

#### Dashboard

[`frontend/app/dashboard/page.tsx`](../frontend/app/dashboard/page.tsx)

Use this file to understand the cross-company view. It loads:

- `/companies`
- `/companies/:id/behavior-summary`
- `/news`
- `/news/review-queue`

#### Company Detail

[`frontend/app/companies/[id]/page.tsx`](../frontend/app/companies/[id]/page.tsx)

Use this file to understand the full data story for one company:

- prices
- floorsheet rows
- behavior summary
- news correlation
- tagged news
- buyer/seller analysis

#### Review Desk

[`frontend/app/review/page.tsx`](../frontend/app/review/page.tsx)

This is the human correction loop for weak categorization results.

#### Admin Console

[`frontend/app/admin/page.tsx`](../frontend/app/admin/page.tsx)

This is where crawl runs are triggered, users are created, and the tracked company watchlist is managed.

## Fastest Way To Understand It End To End

Do one real run with the app open:

1. Login as admin.
2. Trigger a full crawl from `/admin`.
3. Open `/dashboard`.
4. Open one company board.
5. Open `/review`.
6. Come back to the code and trace each UI request back to:
   - the API file
   - the service file
   - the model file

That gives you the best understanding in the shortest time.

## Best Files To Read If You Only Have One Hour

- [`README.md`](../README.md)
- [`backend/app/main.py`](../backend/app/main.py)
- [`backend/app/services/crawl_service.py`](../backend/app/services/crawl_service.py)
- [`backend/app/services/categorization_service.py`](../backend/app/services/categorization_service.py)
- [`backend/app/services/analysis_service.py`](../backend/app/services/analysis_service.py)
- [`frontend/app/dashboard/page.tsx`](../frontend/app/dashboard/page.tsx)
- [`frontend/app/companies/[id]/page.tsx`](../frontend/app/companies/[id]/page.tsx)

## Best Files To Read If You Want Confidence For An Interview Or Demo

- [`backend/tests/test_crawl_service.py`](../backend/tests/test_crawl_service.py)
- [`backend/tests/test_analysis_service.py`](../backend/tests/test_analysis_service.py)
- [`backend/tests/test_companies_api.py`](../backend/tests/test_companies_api.py)
- [`backend/tests/test_admin_api.py`](../backend/tests/test_admin_api.py)
- [`backend/tests/test_news_rbac.py`](../backend/tests/test_news_rbac.py)

Tests tell you what the system is expected to do, which is often faster than reading every implementation file in sequence.
