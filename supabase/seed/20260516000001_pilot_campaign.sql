insert into campaigns (
  slug,
  name,
  subject_template,
  html_template_path,
  utm_campaign,
  daily_cap,
  status,
  dry_run
) values (
  'pilot_50',
  'Pilot — top schools free builder',
  'Free K–12 prompt builder for {{state}} teachers',
  'templates/pilot_50.html',
  'school_pilot_50_2026',
  50,
  'draft',
  true
) on conflict (slug) do nothing;
