-- Classroom Prompt Builder — school outreach (isolated from Vercel fulfillment)
-- Idempotent: safe to re-run on preview branches and existing prod DBs.

create extension if not exists "pgcrypto";

do $$ begin
  create type suppression_reason as enum (
    'hard_bounce',
    'complaint',
    'unsubscribe',
    'soft_bounce',
    'manual'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type contact_role as enum (
    'principal',
    'instructional_coach',
    'media_specialist',
    'generic_office',
    'other'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type outreach_status as enum (
    'pending',
    'ready',
    'sent',
    'bounced',
    'complained',
    'opted_out',
    'replied',
    'skipped'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type campaign_status as enum (
    'draft',
    'active',
    'paused',
    'completed'
  );
exception when duplicate_object then null; end $$;

create table if not exists schools (
  id uuid primary key default gen_random_uuid(),
  nces_id text unique,
  us_news_rank int,
  school_name text not null,
  district_name text,
  city text,
  state char(2),
  zip text,
  grades text,
  enrollment int,
  website_url text,
  domain text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists schools_state_idx on schools (state);
create index if not exists schools_rank_idx on schools (us_news_rank) where us_news_rank is not null;

create table if not exists contacts (
  id uuid primary key default gen_random_uuid(),
  school_id uuid references schools (id) on delete set null,
  email text not null unique,
  role_target contact_role not null default 'generic_office',
  contact_name text,
  email_source text,
  verified_at timestamptz,
  verify_confidence text,
  outreach_status outreach_status not null default 'pending',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists contacts_school_id_idx on contacts (school_id);
create index if not exists contacts_outreach_status_idx on contacts (outreach_status);

create table if not exists suppressions (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  reason suppression_reason not null,
  source_email_id text,
  created_at timestamptz not null default now()
);

create index if not exists suppressions_reason_idx on suppressions (reason);

create table if not exists campaigns (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  subject_template text not null,
  html_template_path text,
  utm_campaign text not null,
  daily_cap int not null default 50,
  status campaign_status not null default 'draft',
  dry_run boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists send_log (
  id uuid primary key default gen_random_uuid(),
  contact_id uuid not null references contacts (id) on delete cascade,
  campaign_id uuid not null references campaigns (id) on delete cascade,
  resend_message_id text,
  status text not null default 'queued',
  error_message text,
  sent_at timestamptz,
  created_at timestamptz not null default now(),
  constraint send_log_contact_campaign unique (contact_id, campaign_id)
);

create index if not exists send_log_campaign_id_idx on send_log (campaign_id);
create index if not exists send_log_resend_message_id_idx on send_log (resend_message_id) where resend_message_id is not null;

create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists schools_updated_at on schools;
create trigger schools_updated_at before update on schools
  for each row execute function set_updated_at();

drop trigger if exists contacts_updated_at on contacts;
create trigger contacts_updated_at before update on contacts
  for each row execute function set_updated_at();

drop trigger if exists campaigns_updated_at on campaigns;
create trigger campaigns_updated_at before update on campaigns
  for each row execute function set_updated_at();

-- RLS: service role only (Railway uses service role key)
alter table schools enable row level security;
alter table contacts enable row level security;
alter table suppressions enable row level security;
alter table campaigns enable row level security;
alter table send_log enable row level security;

drop policy if exists service_role_all_schools on schools;
create policy service_role_all_schools on schools for all using (true) with check (true);

drop policy if exists service_role_all_contacts on contacts;
create policy service_role_all_contacts on contacts for all using (true) with check (true);

drop policy if exists service_role_all_suppressions on suppressions;
create policy service_role_all_suppressions on suppressions for all using (true) with check (true);

drop policy if exists service_role_all_campaigns on campaigns;
create policy service_role_all_campaigns on campaigns for all using (true) with check (true);

drop policy if exists service_role_all_send_log on send_log;
create policy service_role_all_send_log on send_log for all using (true) with check (true);
