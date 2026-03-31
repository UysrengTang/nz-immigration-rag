# Backend Runbook

This backend contains the ingestion pipeline, vector schema, and API scaffold for the NZ Immigration RAG application.

## 1. Prerequisites

- Python 3.11+
- PostgreSQL or Supabase Postgres with `pgvector`
- An OpenAI API key for real embeddings

## 2. Install Dependencies

From the `backend/` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 3. Configure Environment

Copy the example file and fill in the required values:

```bash
cp .env.example .env
```

Required values for a real ingestion run:

- `OPENAI_API_KEY`
- `DATABASE_URL`

Optional but useful:

- `OPENAI_EMBEDDING_DIMENSIONS`
- `LANGSMITH_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

## 4. Apply the Initial Migration

You can apply the initial schema with `psql`:

```bash
psql "$DATABASE_URL" -f app/db/migrations/0001_initial_schema.sql
```

Or paste the migration into the Supabase SQL editor if you are using Supabase-hosted Postgres.

## 5. Run the CLI Ingestion Command

Example: ingest one approved INZ website URL

```bash
python3 -m app.cli.ingest \
  --source-type inz_website \
  --url https://www.immigration.govt.nz/new-zealand-visas \
  --pretty
```

Example: ingest URLs from a file

```bash
python3 -m app.cli.ingest \
  --source-type operational_manual \
  --urls-file urls.txt \
  --pretty
```

The `urls.txt` file should contain one URL per line. Blank lines and lines starting with `#` are ignored.

If the package is installed in editable mode, you can also use the console script:

```bash
nz-rag-ingest --source-type inz_website --urls-file urls.txt --pretty
```

## 6. Start the API Scaffold

The API is still a scaffold, but you can run it locally:

```bash
uvicorn app.main:app --reload
```

Health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

## 7. Current Limitations

- Source loaders currently ingest explicit URLs; there is no crawler or sitemap walker yet.
- HTML extraction is generic and deterministic, not source-specific.
- The chat workflow is still a placeholder and does not run retrieval yet.
- The ingestion path will fail fast if `OPENAI_API_KEY` is not set and no test embedder is injected.
