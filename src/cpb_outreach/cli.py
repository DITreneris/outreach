import json
from pathlib import Path

import click

from cpb_outreach.enrich.import_supabase import enrich_and_import_contacts, import_schools_csv
from cpb_outreach.enrich.merge_nces import build_master
from cpb_outreach.sender import run_campaign_batch


@click.group()
def cli() -> None:
    """CPB school outreach CLI."""


@cli.command("merge-nces")
@click.option("--nces-csv", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--rankings-csv", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--output", type=click.Path(path_type=Path), default=Path("data/schools_master.csv"))
@click.option("--school-pool", default=750, show_default=True, help="Max schools after filters")
@click.option("--level", default="High", show_default=True, help="LEVEL filter (empty to skip)")
@click.option("--open-only/--all-status", default=True, show_default=True)
@click.option("--dedupe-domain/--no-dedupe-domain", default=True, show_default=True)
def merge_nces(
    nces_csv: Path,
    rankings_csv: Path | None,
    output: Path,
    school_pool: int,
    level: str,
    open_only: bool,
    dedupe_domain: bool,
) -> None:
    """Build filtered school pool CSV from NCES directory."""
    output.parent.mkdir(parents=True, exist_ok=True)
    level_filter = level if level else None
    df = build_master(
        nces_csv,
        rankings_csv,
        school_pool=school_pool,
        level=level_filter,
        open_only=open_only,
        dedupe_domain=dedupe_domain,
    )
    df.to_csv(output, index=False)
    click.echo(f"Wrote {len(df)} schools to {output}")


@cli.command("import-schools")
@click.option("--csv", "csv_path", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--batch-size", default=100, show_default=True)
def import_schools(csv_path: Path, batch_size: int) -> None:
    """Upsert schools from merged CSV into Supabase."""
    count = import_schools_csv(csv_path, batch_size=batch_size)
    click.echo(f"Imported {count} schools")


@cli.command("enrich-contacts")
@click.option("--target", "target_contacts", default=500, show_default=True)
@click.option("--school-batch", default=50, show_default=True)
@click.option("--no-scrape", is_flag=True, help="Skip HTTP scrape (DB only)")
def enrich_contacts(target_contacts: int, school_batch: int, no_scrape: bool) -> None:
    """Scrape school sites until target ready contacts in Supabase."""
    result = enrich_and_import_contacts(
        target_contacts=target_contacts,
        school_batch=school_batch,
        scrape=not no_scrape,
    )
    click.echo(json.dumps(result, indent=2))


@cli.command("send-pilot")
@click.option("--slug", default="pilot_50", show_default=True)
@click.option("--limit", default=50, show_default=True)
def send_pilot(slug: str, limit: int) -> None:
    """Run pilot campaign batch (respects campaign dry_run flag)."""
    result = run_campaign_batch(slug, limit=limit)
    click.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    cli()
