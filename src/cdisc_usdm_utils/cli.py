import sys
import json
import click
import importlib.util
from pathlib import Path


def _abs(p: str) -> str:
    return str(Path(p).expanduser().resolve())


@click.group(help="USDM utilities: generate SDTM outputs, Define-XML, and XPT files")
def cli():
    pass


def _default_outdir() -> Path:
    return Path("output").resolve()


def _load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


@cli.group(help="Generate SDTM domain outputs (CSV + Dataset-JSON)")
def sdtm():
    pass


def _load_bin_module(mod_name: str, file_name: str):
    repo_root = Path(__file__).resolve().parents[2]
    file_path = repo_root / "bin" / file_name
    if not file_path.exists():
        raise click.ClickException(f"Script not found: {file_path}")
    spec = importlib.util.spec_from_file_location(mod_name, str(file_path))
    if spec is None or spec.loader is None:
        raise click.ClickException(f"Unable to load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_domain(domain: str, usdm_file: str, out_dir: str):
    out = Path(out_dir) / f"{domain}.csv"
    if domain == "TA":
        from .domains.ta import generate as run_ta

        run_ta(_abs(usdm_file), _abs(str(out)))
    elif domain == "TE":
        from .domains.te import generate as run_te

        run_te(_abs(usdm_file), _abs(str(out)))
    elif domain == "TV":
        from .domains.tv import generate as run_tv

        run_tv(_abs(usdm_file), _abs(str(out)))
    elif domain == "TI":
        from .domains.ti import generate as run_ti

        run_ti(_abs(usdm_file), _abs(str(out)))
    elif domain == "TS":
        from .domains.ts import generate as run_ts

        ts_spec = "spec/TS_defn.csv"
        tsparm_spec = "spec/TSPARM_spec.csv"
        if not Path(tsparm_spec).exists():
            click.echo("Skipping TS: missing spec/TSPARM_spec.csv", err=True)
            return
        run_ts(_abs(usdm_file), _abs(str(out)), _abs(ts_spec), _abs(tsparm_spec))
    else:
        raise click.ClickException(f"Unknown domain: {domain}")


@sdtm.command("all")
@click.option(
    "--usdm-file", required=True, type=click.Path(exists=True), help="USDM JSON"
)
@click.option(
    "--out-dir",
    default=str(_default_outdir()),
    type=click.Path(),
    help="Output directory",
)
def sdtm_all(usdm_file: str, out_dir: str):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    for dom in ["TA", "TE", "TV", "TI", "TS"]:
        click.echo(f"Generating {dom}...")
        _run_domain(dom, usdm_file, out_dir)
    click.echo("Done.")


@sdtm.command()
@click.argument("domain", type=click.Choice(["TA", "TE", "TV", "TI", "TS"]))
@click.option("--usdm-file", required=True, type=click.Path(exists=True))
@click.option("--out-dir", default=str(_default_outdir()), type=click.Path())
def one(domain: str, usdm_file: str, out_dir: str):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    _run_domain(domain, usdm_file, out_dir)
    click.echo(f"Generated {domain}.")


@cli.command(help="Generate Define-XML from SDTM outputs and metadata")
@click.option("--usdm-file", required=True, type=click.Path(exists=True))
@click.option("--out-dir", default=str(_default_outdir()), type=click.Path())
def define(usdm_file: str, out_dir: str):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mod = _load_bin_module("create_define_xml", "create_define_xml.py")
    # Prefer the parameterized generator if available
    if hasattr(mod, "generate_define"):
        mod.generate_define(_abs(usdm_file), _abs(out_dir))
    elif hasattr(mod, "main"):
        # Backward-compat: some versions parse args internally
        mod.main()
    else:
        raise click.ClickException(
            "create_define_xml.py did not expose generate_define(usdm_file, out_dir) or main()"
        )
    click.echo("define.xml generated.")


@cli.command(help="Write XPT files for selected domains from CSV")
@click.option(
    "--domains", multiple=True, type=click.Choice(["TA", "TE", "TV", "TI", "TS"])
)
@click.option("--csv-dir", default=str(_default_outdir()), type=click.Path())
@click.option("--out-dir", default=str(_default_outdir()), type=click.Path())
def xpt(domains, csv_dir: str, out_dir: str):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mod = _load_bin_module("create_xpt", "create_xpt.py")
    if not domains:
        domains = ("TA", "TE", "TV", "TI", "TS")
    if hasattr(mod, "write_xpt_for_domains"):
        mod.write_xpt_for_domains(domains, _abs(csv_dir), _abs(out_dir))
    else:
        raise click.ClickException(
            "create_xpt.py does not expose write_xpt_for_domains(domains, csv_dir, out_dir)"
        )
    click.echo("XPT export complete.")


def main():
    cli(prog_name="usdm-utils")


if __name__ == "__main__":
    sys.exit(main())
