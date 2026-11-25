# NewsApp Backend (Django + DRF)

Dedicated backend for **All Bangla Newspapers: Live BD** (`newsapp`).

## Quick Start

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py seed_newspapers
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

## Add Your Tenant Portals

1. Open `http://127.0.0.1:8000/admin/`.
2. Go to **Feed -> Tenant portals -> Add tenant portal**.
3. Enter your portal's `name`, `slug` (matching `@newspaper` tenant slug), `domain`, and `source_type` (`NEWSPAPER_API` or `WORDPRESS_API`).
4. Select your portals and run the admin action **"Sync latest articles from selected tenant portals"** (or run `python manage.py sync_tenant_news`).

## API Endpoints

- `GET /api/health/` — Health check
- `GET /api/newspapers/` — Active directory newspapers
- `GET /api/trending/` — Live trending carousel headlines (tenant portals only)
- `GET /api/feed/` — Automated tenant stories + active daily poll
- `POST /api/polls/<poll_id>/vote/` — Record a community poll vote
- `POST /api/sync/tenants/` — Trigger sync across all active tenant portals (send `X-Sync-Key` header if `SYNC_API_KEY` is set)
