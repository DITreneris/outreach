# Import 500 contacts into Supabase (local only — requires SERVICE_ROLE in .env)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$SchoolsCsv = if ($env:SCHOOLS_CSV) { $env:SCHOOLS_CSV } else {
    Join-Path $Root "data\nces_raw\schools.csv"
}
if (-not (Test-Path $SchoolsCsv)) {
    $SchoolsCsv = "..\..\06_DI_Operacine_sistema_mokytojui\schools.csv"
}

.\.venv\Scripts\cpb-outreach merge-nces --nces-csv $SchoolsCsv --school-pool 750 --output data\schools_master.csv
.\.venv\Scripts\cpb-outreach import-schools --csv data\schools_master.csv
.\.venv\Scripts\cpb-outreach enrich-contacts --target 500 --school-batch 50
