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


@cli.command(
    help="Extract biomedical concepts (concepts, properties, response codes, surrogates) with filters and multiple formats"
)
@click.option(
    "--usdm-file",
    required=True,
    type=click.Path(exists=True),
    help="USDM JSON input file",
)
@click.option(
    "--out-file",
    default="output/biomedical_concepts.csv",
    type=click.Path(),
    help="Destination CSV (default: output/biomedical_concepts.csv)",
)
@click.option(
    "--json-out",
    type=click.Path(),
    help="Optional JSON output path (array of flattened rows). Skips if not provided.",
)
@click.option(
    "--markdown-tree",
    type=click.Path(),
    help="Optional markdown lineage tree output path; use '-' for stdout (concept -> property -> response code).",
)
@click.option(
    "--include-surrogates/--no-surrogates",
    default=True,
    show_default=True,
    help="Include surrogate concept entries (bcSurrogates).",
)
@click.option(
    "--no-response-codes",
    is_flag=True,
    help="Exclude response code rows (properties' enumerated values).",
)
@click.option(
    "--filter-name",
    help="Case-insensitive substring filter applied to the concept/property name (top-level concepts filtered; their children retained only if parent matches).",
)
@click.option(
    "--filter-reference-prefix",
    help="Only include top-level concepts whose reference starts with this prefix.",
)
@click.option(
    "--filter-code-system",
    help="Only include top-level concepts whose code's codeSystem matches this (case-insensitive).",
)
def concepts(
    usdm_file: str,
    out_file: str,
    json_out: str | None,
    markdown_tree: str | None,
    include_surrogates: bool,
    no_response_codes: bool,
    filter_name: str | None,
    filter_reference_prefix: str | None,
    filter_code_system: str | None,
):
    """Flatten biomedical concepts hierarchy into tabular and optionally JSON / markdown outputs.

    CSV / JSON row columns:
      id, parent_id, name, label, synonyms, reference, code, decode, type

    parent_id is blank for top-level concepts & surrogates; properties reference
    their concept id; response codes reference their property id. "type" marks the
    row's source (BiomedicalConcept, BiomedicalConceptProperty, ResponseCode, surrogate type).
    Filters (name/reference/code system) apply to top-level concepts before expansion.
    """
    try:
        mod = _load_bin_module("biomedical_concepts", "biomedical_concepts.py")
    except click.ClickException as e:
        raise click.ClickException(f"Unable to load biomedical concepts script: {e}")
    # Required functions
    required = [
        "process_usdm_biomedical_concepts_to_csv",
        "concepts_to_json",
        "concepts_markdown_tree",
    ]
    for r in required:
        if not hasattr(mod, r):
            raise click.ClickException(f"biomedical_concepts.py missing {r}()")

    Path(out_file).parent.mkdir(parents=True, exist_ok=True)

    # Generate CSV (always unless user explicitly set an impossible path)
    mod.process_usdm_biomedical_concepts_to_csv(
        _abs(usdm_file),
        _abs(out_file),
        include_surrogates=include_surrogates,
        include_response_codes=not no_response_codes,
        filter_name=filter_name,
        filter_reference_prefix=filter_reference_prefix,
        filter_code_system=filter_code_system,
    )
    click.echo(f"Biomedical concepts written to {out_file}")

    # Optionally produce JSON (single pass for consistency)
    rows = None
    if json_out or markdown_tree:
        rows = mod.concepts_to_json(
            _abs(usdm_file),
            include_surrogates=include_surrogates,
            include_response_codes=not no_response_codes,
            filter_name=filter_name,
            filter_reference_prefix=filter_reference_prefix,
            filter_code_system=filter_code_system,
        )
    if json_out:
        Path(json_out).parent.mkdir(parents=True, exist_ok=True)
        with open(json_out, "w", encoding="utf-8") as jf:
            json.dump(rows, jf, indent=2, ensure_ascii=False)
        click.echo(f"Biomedical concepts JSON written to {json_out}")
    if markdown_tree:
        md_text = mod.concepts_markdown_tree(rows)
        if markdown_tree == "-":
            click.echo(md_text)
        else:
            Path(markdown_tree).parent.mkdir(parents=True, exist_ok=True)
            with open(markdown_tree, "w", encoding="utf-8") as mf:
                mf.write(md_text + "\n")
            click.echo(
                f"Biomedical concepts lineage markdown written to {markdown_tree}"
            )


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
@click.option(
    "--objects-only",
    is_flag=True,
    help="Object-level mode: report only objects (by id) that were added, removed, or changed; suppress field-level detail.",
)
@click.option(
    "--object-id-key",
    "object_id_keys",
    multiple=True,
    help="Custom key name(s) to treat as object identifier (repeat). Defaults: id, ID.",
)
@click.option(
    "--object-id-filter",
    "object_id_filters",
    multiple=True,
    help="Substring filter applied to resolved object id (case-insensitive, repeatable). Only applies with --objects-only.",
)
@click.option(
    "--path-filter",
    "path_filters",
    multiple=True,
    help="Substring/anchored filter(s) applied to change paths before section/object processing. Use ^prefix or suffix$ for anchoring.",
)
@click.option(
    "--fail-on-change",
    is_flag=True,
    help="Exit with status 1 if any changes are detected (object or field level).",
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
    objects_only: bool,
    object_id_keys: tuple[str, ...],
    object_id_filters: tuple[str, ...],
    path_filters: tuple[str, ...],
    fail_on_change: bool,
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

    # Path filtering (pre section/object processing)
    if path_filters:
        raw_filters = [pf for pf in path_filters if pf]

        def _match_path(p: str) -> bool:
            lp = p
            for flt in raw_filters:
                if flt.startswith("^") and flt.endswith("$"):
                    target = flt[1:-1]
                    if lp == target:
                        return True
                elif flt.startswith("^"):
                    if lp.startswith(flt[1:]):
                        return True
                elif flt.endswith("$"):
                    if lp.endswith(flt[:-1]):
                        return True
                else:
                    if flt in lp:
                        return True
            return False

        changes = [c for c in changes if _match_path(c.get("path", ""))]
        if format_text:
            text_report = format_text(changes)
    normalized_sections = _normalize_sections(sections)
    if normalized_sections:
        changes = _apply_section_filter(changes, normalized_sections)
        if format_text:
            text_report = format_text(changes)
    # Optional path & object post-processing helpers

    def _get_json(path: str) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    a_json = None
    b_json = None

    def _split_segments(p: str) -> list[str]:
        if not p or p == "/":
            return []
        segs = []
        for part in p.strip("/").split("/"):
            if part:
                segs.append(part)
        return segs

    def _descend(root: Any, segments: list[str]) -> Any:
        cur = root
        for seg in segments:
            # parse like name[0] or name
            if "[" in seg and seg.endswith("]"):
                base = seg[: seg.index("[")]
                idx_str = seg[seg.index("[") + 1 : -1]
                if base:
                    cur = cur.get(base) if isinstance(cur, dict) else None  # type: ignore
                if cur is None:
                    return None
                try:
                    idx = int(idx_str)
                except ValueError:
                    return None
                if isinstance(cur, list) and 0 <= idx < len(cur):
                    cur = cur[idx]
                else:
                    return None
            else:
                if isinstance(cur, dict):
                    cur = cur.get(seg)
                else:
                    return None
            if cur is None:
                return None
        return cur

    def _find_object_root(
        path: str, id_keys: list[str], root_a: Any, root_b: Any
    ) -> str | None:
        segs = _split_segments(path)
        # ascend until object dict with id key found in either version
        for i in range(len(segs), 0, -1):
            cand_path_segs = segs[:i]
            cand_path = "/" + "/".join(cand_path_segs)
            node_a = _descend(root_a, cand_path_segs) if root_a is not None else None
            node_b = _descend(root_b, cand_path_segs) if root_b is not None else None
            for k in id_keys:
                if isinstance(node_a, dict) and k in node_a and node_a[k] is not None:
                    return cand_path
                if isinstance(node_b, dict) and k in node_b and node_b[k] is not None:
                    return cand_path
        return None

    def _object_changes(ch_list: list[dict], id_keys: list[str]) -> list[dict]:
        nonlocal a_json, b_json
        if a_json is None:
            a_json = _get_json(file1)
        if b_json is None:
            b_json = _get_json(file2)
        roots: dict[str, dict] = {}
        for ch in ch_list:
            p = ch.get("path", "")
            root_path = _find_object_root(p, id_keys, a_json, b_json)
            if not root_path:
                continue
            roots.setdefault(root_path, {"changes": 0})
            roots[root_path]["changes"] += 1
        results: list[dict] = []
        for op_path, meta in roots.items():
            segs = _split_segments(op_path)
            node_a = _descend(a_json, segs)
            node_b = _descend(b_json, segs)
            # determine op
            if node_a is None and node_b is not None:
                op = "add"
            elif node_b is None and node_a is not None:
                op = "remove"
            else:
                op = "change"
            # id resolution
            oid = None
            id_key_used = None
            for k in id_keys:
                if isinstance(node_b, dict) and k in node_b and node_b[k] is not None:
                    oid = node_b[k]
                    id_key_used = k
                    break
                if isinstance(node_a, dict) and k in node_a and node_a[k] is not None:
                    oid = node_a[k]
                    id_key_used = k
                    break
            results.append(
                {
                    "op": op,
                    "path": op_path,
                    "id": oid,
                    "idKey": id_key_used,
                    "fieldsChanged": meta["changes"],
                    "old": node_a if op != "add" else None,
                    "new": node_b if op != "remove" else None,
                }
            )
        return sorted(results, key=lambda r: r["path"])

    id_key_list = [*object_id_keys] if object_id_keys else ["id", "ID"]

    # Track whether differences exist for potential CI gating later
    diff_found = False
    # Store flag on function (used after output writing without altering earlier structure)
    diff._fail_on_change = fail_on_change  # type: ignore[attr-defined]

    if objects_only:
        object_level = _object_changes(changes, id_key_list)
        # Apply id filters if provided
        if object_id_filters:
            flt = [s.lower() for s in object_id_filters if s]
            object_level = [
                o
                for o in object_level
                if (
                    o.get("id") is not None
                    and any(sub in str(o.get("id")).lower() for sub in flt)
                )
            ]
        # Replace changes with object-level abstraction
        changes = object_level
        # Build a textual representation similar to existing style
        lines = []
        add = sum(1 for c in changes if c["op"] == "add")
        rem = sum(1 for c in changes if c["op"] == "remove")
        chg = sum(1 for c in changes if c["op"] == "change")
        diff_found = (add + rem + chg) > 0
        summary_line = f"Objects Added: {add}  Removed: {rem}  Changed: {chg}  Total: {len(changes)}"
        if object_id_filters:
            summary_line += f" (filtered by {', '.join(object_id_filters)})"
        lines.append(summary_line)
        for c in changes:
            marker = "+" if c["op"] == "add" else ("-" if c["op"] == "remove" else "~")
            ident = f" {c['idKey']}={c['id']}" if c.get("id") is not None else ""
            extra = (
                f" ({c['fieldsChanged']} field change(s))"
                if c["op"] == "change"
                else ""
            )
            line = f"{marker} {c['path']}{ident}{extra}"
            lines.append(line)
        text_report = "\n".join(lines)

    # Build summary structures
    if objects_only:
        # Provide a summary dict consistent with field-level mode so JSON pipelines remain uniform
        obj_add = sum(1 for c in changes if c["op"] == "add")
        obj_rem = sum(1 for c in changes if c["op"] == "remove")
        obj_chg = sum(1 for c in changes if c["op"] == "change")
        summ = {
            "added": obj_add,
            "removed": obj_rem,
            "changed": obj_chg,
            "typeMismatches": 0,
            "total": obj_add + obj_rem + obj_chg,
        }
    else:
        summ = summarize(changes) if summarize else None
        if summ:
            diff_found = summ.get("total", 0) > 0
    group_summ = (
        _build_group_summary(changes, group_summary_flag) if not objects_only else None
    )

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
        if objects_only:
            payload["mode"] = "objects"
            payload["idKeys"] = id_key_list
            if object_id_filters:
                payload["idFilters"] = list(object_id_filters)
            if path_filters:
                payload["pathFilters"] = list(path_filters)
            if summary_only:
                # Provide per-object details (id, op, fieldsChanged) without full object payloads
                payload["objectDetails"] = [
                    {
                        k: o[k]
                        for k in ("op", "path", "id", "idKey", "fieldsChanged")
                        if k in o
                    }
                    for o in changes
                ]
                payload["totalFieldChanges"] = sum(
                    (o.get("fieldsChanged") or 0)
                    for o in changes
                    if o.get("op") == "change"
                )
        out_text = json.dumps(payload, indent=2)
    else:
        if summary_only:
            if objects_only:
                # summary-only in objects mode already built into first line of text_report
                out_text = text_report.splitlines()[0] if text_report else ""
            else:
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
        if color != "never" and not markdown:
            enable = color == "always" or (color == "auto" and sys.stdout.isatty())
            if enable:
                if colorize_text and not objects_only:
                    out_text = colorize_text(
                        out_text, True
                    )  # field-level existing coloring
                elif objects_only:
                    # Simple inline coloring for objects-only markers
                    colored_lines = []
                    for ln in out_text.splitlines():
                        if ln.startswith("+ "):
                            colored_lines.append(f"\x1b[32m{ln}\x1b[0m")
                        elif ln.startswith("- "):
                            colored_lines.append(f"\x1b[31m{ln}\x1b[0m")
                        elif ln.startswith("~ "):
                            colored_lines.append(f"\x1b[33m{ln}\x1b[0m")
                        elif ln.startswith("Objects Added:"):
                            colored_lines.append(f"\x1b[36m{ln}\x1b[0m")
                        else:
                            colored_lines.append(ln)
                    out_text = "\n".join(colored_lines)

    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            f.write(out_text + "\n")
        click.echo(f"Diff report written to {output}")
    else:
        click.echo(out_text)

    # Deferred import to avoid circular if we add the option above (keeping patch minimal)
    # Fail-on-change support: we intentionally pick up an env-style flag until CLI option added.
    # (Will be wired through a proper click option below.)
    if getattr(diff, "_fail_on_change", False) and diff_found:
        raise click.exceptions.Exit(1)


def main():
    cli(prog_name="usdm-utils")


@cli.command(
    "diff-html",
    help="Generate side-by-side HTML diff for changed objects (field-level changes collapsed per object)",
)
@click.argument("file1", type=click.Path(exists=True))
@click.argument("file2", type=click.Path(exists=True))
@click.option("--output", required=True, type=click.Path(), help="HTML file to write")
@click.option(
    "--list-key", help="Align list objects by this key (reduces positional churn)"
)
@click.option(
    "--object-id-key",
    "object_id_keys",
    multiple=True,
    help="Custom object id key(s) (repeat). Defaults: id, ID",
)
def diff_html(
    file1: str,
    file2: str,
    output: str,
    list_key: str | None,
    object_id_keys: tuple[str, ...],
):
    if diff_usdm_json is None:
        raise click.ClickException("Diff utility not available")

    changes, _ = diff_usdm_json(file1, file2, list_key=list_key)

    # Load full JSONs for value extraction
    with open(file1, "r", encoding="utf-8") as f:
        a_json = json.load(f)
    with open(file2, "r", encoding="utf-8") as f:
        b_json = json.load(f)

    id_key_list = [*object_id_keys] if object_id_keys else ["id", "ID"]

    # Helpers (reuse subset of functions from diff command)
    def split_segments(p: str) -> list[str]:
        if not p or p == "/":
            return []
        segs = []
        for part in p.strip("/").split("/"):
            if part:
                segs.append(part)
        return segs

    def descend(root: Any, segments: list[str]) -> Any:
        cur = root
        for seg in segments:
            if "[" in seg and seg.endswith("]"):
                base = seg[: seg.index("[")]
                idx_str = seg[seg.index("[") + 1 : -1]
                if base:
                    cur = cur.get(base) if isinstance(cur, dict) else None  # type: ignore
                if cur is None:
                    return None
                try:
                    idx = int(idx_str)
                except ValueError:
                    return None
                if isinstance(cur, list) and 0 <= idx < len(cur):
                    cur = cur[idx]
                else:
                    return None
            else:
                if isinstance(cur, dict):
                    cur = cur.get(seg)
                else:
                    return None
            if cur is None:
                return None
        return cur

    def find_object_root(path: str) -> str | None:
        segs = split_segments(path)
        for i in range(len(segs), 0, -1):
            cand = segs[:i]
            node_a = descend(a_json, cand)
            node_b = descend(b_json, cand)
            for k in id_key_list:
                if isinstance(node_a, dict) and k in node_a and node_a[k] is not None:
                    return "/" + "/".join(cand)
                if isinstance(node_b, dict) and k in node_b and node_b[k] is not None:
                    return "/" + "/".join(cand)
        return None

    # Group field-level changes by object root
    by_object: dict[str, list[dict]] = {}
    for ch in changes:
        p = ch.get("path", "")
        root = find_object_root(p)
        if not root:
            continue
        by_object.setdefault(root, []).append(ch)

    # Build object records with old/new snapshots
    rows: list[dict[str, Any]] = []
    for obj_path, ch_list in by_object.items():
        segs = split_segments(obj_path)
        node_a = descend(a_json, segs)
        node_b = descend(b_json, segs)
        oid = None
        id_used = None
        for k in id_key_list:
            if isinstance(node_b, dict) and k in node_b and node_b[k] is not None:
                oid = node_b[k]
                id_used = k
                break
            if isinstance(node_a, dict) and k in node_a and node_a[k] is not None:
                oid = node_a[k]
                id_used = k
                break
        rows.append(
            {
                "path": obj_path,
                "id": oid,
                "idKey": id_used,
                "changes": len(ch_list),
                "old": node_a,
                "new": node_b,
            }
        )

    # Sort rows by path
    rows.sort(key=lambda r: r["path"])

    # HTML rendering
    def html_escape(s: str) -> str:
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def json_block(obj: Any) -> str:
        if obj is None:
            return '<div class="null">∅</div>'
        try:
            txt = json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True)
        except Exception:
            txt = str(obj)
        return f"<pre>{html_escape(txt)}</pre>"

    summary = f"Total Objects Changed: {len(rows)}"
    head = (
        f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>USDM Diff</title>"
        "<style>body{font-family:system-ui,Arial,sans-serif;margin:1rem;}table{border-collapse:collapse;width:100%;margin-bottom:1.5rem;}"
        "th,td{border:1px solid #ccc;padding:6px;vertical-align:top;font-size:13px;}th{background:#f5f5f5;}"
        "tr:nth-child(even){background:#fafafa;}code,pre{font-family:ui-monospace,Menlo,monospace;font-size:12px;}"
        ".meta{font-size:12px;color:#555;margin-bottom:1rem;}h2{margin:1.2rem 0 0.4rem;} .null{color:#999;font-style:italic;} .idbadge{background:#eef;padding:2px 6px;border-radius:4px;font-size:11px;}"
        "</style></head><body>"
    )
    parts = [head, f"<h1>USDM Object Diff</h1>", f"<div class='meta'>{summary}</div>"]

    for r in rows:
        ident = (
            f" <span class='idbadge'>{r['idKey']}={html_escape(str(r['id']))}</span>"
            if r.get("id") is not None
            else ""
        )
        parts.append(f"<h2>{html_escape(r['path'])}{ident}</h2>")
        parts.append(f"<div class='meta'>{r['changes']} field-level change(s)</div>")
        parts.append(
            "<table><thead><tr><th style='width:50%'>Old</th><th style='width:50%'>New</th></tr></thead><tbody>"
        )
        parts.append(
            "<tr><td>"
            + json_block(r["old"])
            + "</td><td>"
            + json_block(r["new"])
            + "</td></tr>"
        )
        parts.append("</tbody></table>")

    parts.append("</body></html>")
    html = "".join(parts)

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)
    click.echo(f"HTML diff written to {output} ({len(rows)} object(s))")


if __name__ == "__main__":
    sys.exit(main())
