-- Variant C subject for pilot_50: identity-led, no "Free" trigger.
-- Idempotent: re-runs do not break.
update campaigns
set subject_template = 'Quick look for {{state}} schools — 30 seconds'
where slug = 'pilot_50';
