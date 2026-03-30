-- Initial schema for the NZ immigration RAG backend.
-- This migration creates the core ingestion, retrieval, and evaluation tables.
--
-- Note on pgvector indexing:
-- The embedding column is declared as `vector` without a fixed dimension so the
-- embedding model can be finalized later. Create the ANN index in a follow-up
-- migration once the embedding dimension is locked.

create extension if not exists vector;
create extension if not exists pgcrypto;

create type source_type as enum (
    'inz_website',
    'operational_manual'
);

create type document_status as enum (
    'active',
    'superseded',
    'failed'
);

create type ingestion_status as enum (
    'pending',
    'running',
    'completed',
    'failed'
);

create type evaluation_status as enum (
    'pending',
    'running',
    'completed',
    'failed'
);

create or replace function set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create table if not exists documents (
    id uuid primary key default gen_random_uuid(),
    source_id text not null,
    source_type source_type not null,
    title text not null,
    url text not null,
    canonical_url text not null,
    section_path jsonb,
    raw_content text not null,
    cleaned_content text not null,
    content_hash text not null,
    authority_rank integer not null default 100,
    effective_date timestamptz,
    scraped_at timestamptz not null,
    status document_status not null default 'active',
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (canonical_url),
    unique (source_type, source_id)
);

create table if not exists document_sections (
    id uuid primary key default gen_random_uuid(),
    document_id uuid not null references documents(id) on delete cascade,
    parent_section_id uuid references document_sections(id) on delete cascade,
    section_key text not null,
    heading text,
    section_path_text text not null,
    level integer not null check (level >= 0),
    ordinal integer not null check (ordinal >= 0),
    body_text text not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (document_id, section_key)
);

create table if not exists chunks (
    id uuid primary key default gen_random_uuid(),
    document_id uuid not null references documents(id) on delete cascade,
    section_id uuid references document_sections(id) on delete set null,
    chunk_index integer not null check (chunk_index >= 0),
    chunk_text text not null,
    chunk_text_tsv tsvector generated always as (to_tsvector('english', chunk_text)) stored,
    token_count integer not null check (token_count >= 0),
    embedding vector,
    title text not null,
    url text not null,
    section_label text,
    source_type source_type not null,
    authority_rank integer not null default 100,
    effective_date timestamptz,
    content_hash text not null,
    prev_chunk_id uuid references chunks(id) on delete set null,
    next_chunk_id uuid references chunks(id) on delete set null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (document_id, chunk_index)
);

create table if not exists ingestion_runs (
    id uuid primary key default gen_random_uuid(),
    status ingestion_status not null,
    source_count integer not null default 0,
    document_count integer not null default 0,
    chunk_count integer not null default 0,
    error_summary text,
    metadata jsonb not null default '{}'::jsonb,
    started_at timestamptz not null default now(),
    completed_at timestamptz
);

create table if not exists ingestion_run_items (
    id uuid primary key default gen_random_uuid(),
    ingestion_run_id uuid not null references ingestion_runs(id) on delete cascade,
    source_type source_type not null,
    source_locator text not null,
    status ingestion_status not null,
    document_id uuid references documents(id) on delete set null,
    content_hash text,
    error_message text,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists evaluation_runs (
    id uuid primary key default gen_random_uuid(),
    dataset_name text not null,
    status evaluation_status not null,
    metrics jsonb not null default '{}'::jsonb,
    started_at timestamptz not null default now(),
    completed_at timestamptz
);

create table if not exists evaluation_results (
    id uuid primary key default gen_random_uuid(),
    evaluation_run_id uuid not null references evaluation_runs(id) on delete cascade,
    example_id text not null,
    query text not null,
    expected_outcome text,
    actual_answer text,
    actual_grounded boolean,
    actual_refusal boolean,
    citation_coverage_score numeric,
    groundedness_score numeric,
    evaluator_notes text,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_documents_source_type on documents(source_type);
create index if not exists idx_documents_status on documents(status);
create index if not exists idx_documents_scraped_at on documents(scraped_at desc);
create index if not exists idx_documents_content_hash on documents(content_hash);

create index if not exists idx_document_sections_document_id on document_sections(document_id);
create index if not exists idx_document_sections_parent_section_id on document_sections(parent_section_id);
create index if not exists idx_document_sections_ordinal on document_sections(ordinal);

create index if not exists idx_chunks_document_id on chunks(document_id);
create index if not exists idx_chunks_section_id on chunks(section_id);
create index if not exists idx_chunks_source_type on chunks(source_type);
create index if not exists idx_chunks_authority_rank on chunks(authority_rank);
create index if not exists idx_chunks_content_hash on chunks(content_hash);
create index if not exists idx_chunks_chunk_text_tsv on chunks using gin(chunk_text_tsv);

create index if not exists idx_ingestion_runs_status on ingestion_runs(status);
create index if not exists idx_ingestion_runs_started_at on ingestion_runs(started_at desc);

create index if not exists idx_ingestion_run_items_ingestion_run_id on ingestion_run_items(ingestion_run_id);
create index if not exists idx_ingestion_run_items_status on ingestion_run_items(status);
create index if not exists idx_ingestion_run_items_source_type on ingestion_run_items(source_type);

create index if not exists idx_evaluation_runs_dataset_name on evaluation_runs(dataset_name);
create index if not exists idx_evaluation_runs_status on evaluation_runs(status);

create index if not exists idx_evaluation_results_evaluation_run_id on evaluation_results(evaluation_run_id);
create index if not exists idx_evaluation_results_example_id on evaluation_results(example_id);

drop trigger if exists trg_documents_updated_at on documents;
create trigger trg_documents_updated_at
before update on documents
for each row execute function set_updated_at();

drop trigger if exists trg_chunks_updated_at on chunks;
create trigger trg_chunks_updated_at
before update on chunks
for each row execute function set_updated_at();
