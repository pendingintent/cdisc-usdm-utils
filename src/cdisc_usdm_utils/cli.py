import sys
import json
from typing import Any
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


try:
    from .usdm_diff import (
        diff_usdm_json,
        format_text,
        format_markdown,
        summarize,
        group_summary,
        colorize_text,
    )
except Exception:
    diff_usdm_json = None  # type: ignore
    format_text = None  # type: ignore
    format_markdown = None  # type: ignore
    summarize = None  # type: ignore
    group_summary = None  # type: ignore
    colorize_text = None  # type: ignore


@cli.command(help="Compare two USDM JSON files; shows summary and differences.")
@click.argument("file1", type=click.Path(exists=True))
@click.argument("file2", type=click.Path(exists=True))
@click.option(
    "--output", type=click.Path(), help="Write report to file instead of stdout"
)
@click.option(
    "--json", "as_json", is_flag=True, help="Emit structured JSON diff instead of text"
)
@click.option(
    "--list-key",
    help="Key name to align objects in lists (e.g. ID) to reduce positional noise",
)
@click.option(
    "--summary-only",
    is_flag=True,
    help="Only emit summary counts (text or JSON depending on mode)",
)
@click.option(
    "--markdown",
    is_flag=True,
    help="Emit markdown table (ignored if --json)",
)
@click.option(
    "--color",
    type=click.Choice(["auto", "always", "never"]),
    default="auto",
    help="Colorize text output (not applied to JSON/markdown).",
)
@click.option(
    "--group-summary",
    "group_summary_flag",
    is_flag=True,
    help="Include grouping of counts by top-level section.",
)
@click.option(
    "--section",
    "sections",
    multiple=True,
    help="Filter to one or more top-level sections (repeat flag). Each value may also be a deep path; only its first segment is used.",
)
@click.option(
    "--group-sort",
    type=click.Choice(["asc", "desc"]),
    default=None,
    help="Sort group summary by total count (asc or desc).",
)
def diff(
    file1: str,
    file2: str,
    output: str | None,
    as_json: bool,
    list_key: str | None,
    summary_only: bool,
    markdown: bool,
    color: str,
    group_summary_flag: bool,
    sections: tuple[str, ...],
    group_sort: str | None,
):
    if diff_usdm_json is None:
        raise click.ClickException("Diff utility not available")

    def _normalize_sections(vals: tuple[str, ...]) -> list[str]:
        out: list[str] = []
        for raw in vals:
            if not raw:
                continue
            r = raw.strip()
            if r.startswith("/"):
                r = r[1:]
            if r.startswith("["):
                out.append("__root_list__")
                continue
            top = r.split("/", 1)[0]
            if top and top != ".":
                out.append(top)
        # de-duplicate preserving order
        seen: set[str] = set()
        ordered: list[str] = []
        for s in out:
            if s not in seen:
                seen.add(s)
                ordered.append(s)
        return ordered

    def _section_of(path: str) -> str:
        if not path or path == "/":
            return "__root__"
        p = path[1:] if path.startswith("/") else path
        if p.startswith("["):
            return "__root_list__"
        return p.split("/", 1)[0]

    def _apply_section_filter(
        changes_list: list[dict], norm_sections: list[str]
    ) -> list[dict]:
        if not norm_sections:
            return changes_list
        return [
            c for c in changes_list if _section_of(c.get("path", "")) in norm_sections
        ]

    def _build_group_summary(changes_list: list[dict], want: bool) -> dict | None:
        if not want or not group_summary:
            return None
        gs = group_summary(changes_list)  # type: ignore
        if group_sort and gs:
            rev = group_sort == "desc"
            items = sorted(gs.items(), key=lambda kv: kv[1]["total"], reverse=rev)
            gs = {k: v for k, v in items}
        return gs

    def _format_summary_line(s: dict | None) -> str:
        if not s:
            return ""
        return (
            f"Added: {s['added']}  Removed: {s['removed']}  Changed: {s['changed']}  "
            f"Type Mismatch: {s['typeMismatches']}  Total: {s['total']}"
        )

    def _append_group_markdown(base: str, gs: dict) -> str:
        lines = [
            base,
            "",
            "### Group Summary",
            "",
            "| Section | Added | Removed | Changed | Type | Total |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for sec, cs in gs.items():
            lines.append(
                f"| {sec} | {cs['added']} | {cs['removed']} | {cs['changed']} | {cs['typeMismatches']} | {cs['total']} |"
            )
        return "\n".join(lines)

    def _append_group_text(base: str, gs: dict) -> str:
        lines = [base, "", "Group Summary:"]
        for sec, cs in gs.items():
            lines.append(
                f"  {sec}: +{cs['added']} -{cs['removed']} ~{cs['changed']} !{cs['typeMismatches']} (total {cs['total']})"
            )
        return "\n".join(lines)

    # Core flow
    changes, text_report = diff_usdm_json(file1, file2, list_key=list_key)
    normalized_sections = _normalize_sections(sections)
    if normalized_sections:
        changes = _apply_section_filter(changes, normalized_sections)
        if format_text:
            text_report = format_text(changes)
    summ = summarize(changes) if summarize else None
    group_summ = _build_group_summary(changes, group_summary_flag)

    if as_json:
        payload: dict[str, Any] = {
            "summary": summ,
            "listKey": list_key,
            "changes": ([] if summary_only else changes),
        }
        if group_summ:
            payload["groupSummary"] = group_summ
        if normalized_sections:
            payload["filteredSections"] = normalized_sections
        out_text = json.dumps(payload, indent=2)
    else:
        if summary_only:
            out_text = _format_summary_line(summ)
        elif markdown:
            base_md = format_markdown(changes) if format_markdown else text_report
            out_text = (
                _append_group_markdown(base_md, group_summ) if group_summ else base_md
            )
        else:
            base_text = text_report
            if group_summ and not summary_only:
                base_text = _append_group_text(base_text, group_summ)
            out_text = base_text
        if color != "never" and not markdown and colorize_text:
            enable = color == "always" or (color == "auto" and sys.stdout.isatty())
            out_text = colorize_text(out_text, enable)

    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            f.write(out_text + "\n")
        click.echo(f"Diff report written to {output}")
    else:
        click.echo(out_text)


def main():
    cli(prog_name="usdm-utils")


if __name__ == "__main__":
    sys.exit(main())
