# Eventory (Vercel edition)

A Vercel-ready fork of the Eventory Flask app. The original container-based
setup targets a local Postgres and local filesystem; this version is wired for
Vercel's serverless Python runtime:

- WSGI entry in `api/index.py`
- Managed Postgres via `DATABASE_URL` (Neon recommended)
- Product image uploads go to Vercel Blob
- Chatbot FAISS index is pre-built offline and shipped in `vector_index/`

## One-time setup

1. **Create a Neon database** at <https://neon.tech>. Copy the pooled
   connection string — it looks like
   `postgresql://user:pwd@ep-xyz.neon.tech/neondb?sslmode=require`.

2. **Seed the schema and sample data**:
   ```sh
   ./scripts/seed_neon.sh "postgresql://...your-neon-url..."
   ```
   You'll need `psql` installed locally.

3. **Build the chatbot vector index** (requires a Google AI Studio key):
   ```sh
   export DATABASE_URL="postgresql://...your-neon-url..."
   export GOOGLE_API_KEY="..."
   pip install -r requirements.txt
   python scripts/build_vector_index.py
   ```
   The script writes `vector_index/index.faiss` and `vector_index/index.pkl`.
   Commit both files — the deploy loads them at cold start.

4. **Link the Vercel project**:
   ```sh
   npm i -g vercel
   vercel link
   ```
   In the dashboard, attach a **Blob** store to the project (the
   `BLOB_READ_WRITE_TOKEN` env var is injected automatically).

5. **Set the remaining env vars** in the Vercel dashboard (Settings → Environment Variables):
   - `DATABASE_URL` — the Neon URL
   - `SECRET_KEY` — any long random string
   - `GOOGLE_API_KEY` — your Google AI Studio key

6. **Deploy**:
   ```sh
   vercel --prod
   ```

## Local development

```sh
cp .env.example .env   # fill in the values
pip install -r requirements.txt
vercel dev             # runs the app on http://localhost:3000
```

`vercel dev` emulates the routing from `vercel.json`, including static asset
pass-through.

## Changing seed data / schema

Edit `db/create.sql` and the CSVs under `db/data/`, then re-run
`./scripts/seed_neon.sh $DATABASE_URL`. If product data changes, regenerate
the vector index afterwards:
`python scripts/build_vector_index.py`.

## What changed vs. the upstream repo

- `app/config.py` — prefers `DATABASE_URL`, falls back to the legacy `DB_*` vars
- `app/db.py` — SQLAlchemy engine uses `NullPool` (serverless-friendly)
- `app/inventory.py` — image uploads go through `app.storage.upload_product_image` (Vercel Blob)
- `app/tools.py` — new `image_url()` helper handles both legacy static paths and absolute Blob URLs
- `app/models/chatbot.py` — loads FAISS from `vector_index/` instead of embedding at request time
- Removed `install.sh`, `db/setup.sh`, `poetry.lock`, the Duke/container docs
- Added `vercel.json`, `api/index.py`, `requirements.txt`, `scripts/`
