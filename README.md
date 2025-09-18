[![Smoke SDTM](https://github.com/pendingintent/cdisc-usdm-utils/actions/workflows/smoke.yml/badge.svg)](https://github.com/pendingintent/cdisc-usdm-utils/actions/workflows/smoke.yml)

# cdisc-usdm-utils

This repo holds utilities relating to USDM activities

# cdisc-usdm-utils

Utilities to generate SDTM domain outputs (CSV + Dataset-JSON v1.1), and XPT files from USDM.

## Quick start

- macOS/Linux, Python 3.10+
- Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# optional but recommended to get the CLI entrypoint installed
pip install -e .
```

If you don't install the package (editable), you can still run via `python -m cdisc_usdm_utils.cli ...` instead of `usdm-utils ...`.

## Generate SDTM domains

Generate all domains (TA, TE, TV, TI, TS):

```bash
usdm-utils sdtm all --usdm-file files/pilot_LLZT_protocol.json --out-dir output
```

Generate a single domain:

```bash
usdm-utils sdtm one TA --usdm-file files/pilot_LLZT_protocol.json --out-dir output
```

Outputs:

- CSV: `output/<DOMAIN>.csv`
- Dataset-JSON v1.1: `output/<DOMAIN>.dataset.json`

Validation:

- A lightweight structural check runs for every Dataset-JSON.
- If `files/dataset.schema.json` is present, JSON Schema validation runs too.
- Any problems are written next to the JSON as `*.errors.txt` and/or `*.schema.errors.txt`.

Notes for TS:

- TS generation expects `spec/TSPARM_spec.csv`. If missing, TS is skipped with a console message.

## Export XPT (SAS V5 transport)

Write XPT files from the generated CSVs:

```bash
usdm-utils xpt --domains TA --domains TE --domains TV --domains TI --domains TS \
	--csv-dir output --out-dir output/xpt
```

Requirements: `pyreadstat` (installed via `requirements.txt`). Column names are trimmed to XPT limits automatically.

## Generate Define-XML

```bash
usdm-utils define --usdm-file files/pilot_LLZT_protocol.json --out-dir output
```

This wraps the existing Define generator and writes `define.xml` under `output/`.

## Extract Biomedical Concepts

Flatten biomedical concepts, their properties, response codes, and surrogates into a single CSV (now with filtering, JSON output, and lineage markdown):

```bash
usdm-utils concepts --usdm-file files/pilot_LLZT_protocol.json --out-file output/biomedical_concepts.csv
```

CSV / JSON row columns:

- id: Unique identifier of the concept / property / response code / surrogate
- parent_id: Blank for top-level concepts & surrogates; property rows point to the concept id; response code rows point to the property id
- name, label: Display attributes if present
- synonyms: Comma-separated list (only populated for top-level concepts currently)
- reference: Concept or surrogate reference (blank for response codes)
- code, decode: Standard code values when available
- type: Row type (BiomedicalConcept, BiomedicalConceptProperty, ResponseCode, surrogate concept type)

Example head preview with pandas:

```bash
python - <<'PY'
import pandas as pd
df = pd.read_csv('output/biomedical_concepts.csv')
print(df.head())
print('Concept rows:', (df.parent_id=='').sum(), 'Total rows:', len(df))
PY
```

If you omit --out-file the default path is `output/biomedical_concepts.csv`.

### Advanced options

```
usdm-utils concepts --usdm-file files/pilot_LLZT_protocol.json \
	--out-file output/biomedical_concepts.csv \
	--json-out output/biomedical_concepts.json \
	--markdown-tree output/biomedical_concepts.md \
	--filter-name Consent \
	--filter-reference-prefix /mdr/bc/ \
	--filter-code-system ncit \
	--no-response-codes \
	--no-surrogates
```

Flags / filters:

- `--include-surrogates/--no-surrogates` (default include): control inclusion of surrogate concepts.
- `--no-response-codes`: omit response code (enumerated value) rows.
- `--json-out <path>`: write the flattened rows as JSON array.
- `--markdown-tree <path or ->`: write a hierarchical lineage tree (use `-` for stdout).
- `--filter-name <substr>`: case-insensitive substring match on top-level concept name (children only retained if parent matches).
- `--filter-reference-prefix <prefix>`: only include concepts whose `reference` starts with this.
- `--filter-code-system <name>`: only include concepts whose standard code `codeSystem` (or `system`) matches (case-insensitive).

Empty filter results produce a header-only CSV, `[]` JSON (when requested), and a markdown file with only the title.

Lineage markdown example (excerpt):

```
# Biomedical Concepts Lineage

- **Adverse Event Prespecified** *BiomedicalConcept* (code: C179175)
	- **AEACN** *BiomedicalConceptProperty* (code: C83013)
	- **AEACNOTH** *BiomedicalConceptProperty* (code: C83109)
	- **AECONTRT** *BiomedicalConceptProperty* (code: C83199)
		- **RC_C49487** *ResponseCode* (code: C49487)
		- **RC_C49488** *ResponseCode* (code: C49488)
```

You can post-filter, e.g. only properties:

```bash
awk -F',' 'NR==1 || $2 != ""' output/biomedical_concepts.csv > output/properties_only.csv
```

## Quick diff examples

Basic text diff (auto color):

```bash
usdm-utils diff files/pilot_LLZT_protocol.json files/pilot_LLZT_protocol_amendment.json
```

JSON summary only (machine friendly):

```bash
usdm-utils diff files/pilot_LLZT_protocol.json files/pilot_LLZT_protocol_amendment.json \
	--json --summary-only > diff_summary.json
```

Markdown (for PR description):

```bash
usdm-utils diff files/pilot_LLZT_protocol.json files/pilot_LLZT_protocol_amendment.json \
	--markdown --group-summary --group-sort desc > DIFF.md
```

Filter to specific sections (multi flag) and align lists by id:

```bash
usdm-utils diff files/pilot_LLZT_protocol.json files/pilot_LLZT_protocol_amendment.json \
	--section Study --section Design --list-key id --group-summary
```

Deep path normalization (treated as top-level Study):

```bash
usdm-utils diff old.json new.json --section /Study/Versions[0]/studyDesigns[0]

#### Deeper grouped summaries (`--group-depth`)

You can expand grouped change aggregation beyond the top-level segment using `--group-depth N` (default 1). The grouping logic:

- Splits each change path into segments (removing the leading `/`).
- Strips list indexes (e.g. `activities[3]` -> `activities`).
- Takes the first N normalized segments and joins them with `.`.
- Root path becomes `__root__`; a path starting with `[` at root becomes `__root_list__`.

Example (depth 3):

```
usdm-utils diff files/pilot_LLZT_amendment_10SEP25.json files/pilot_LLZT_amendment_11SEP25.json \
	--group-summary --group-depth 3 --summary-only
```

Sample output excerpt:

```
Added: 4  Removed: 0  Changed: 4686  Type Mismatch: 0  Total: 4690
Group Summary:
	study.versions.biomedicalConcepts: +0 -0 ~4345 !0 (total 4345)
	study.versions.studyDesigns: +2 -0 ~180 !0 (total 182)
	study.versions.bcSurrogates: +1 -0 ~100 !0 (total 101)
	study.versions.studyInterventions: +0 -0 ~26 !0 (total 26)
	study.versions.amendments: +1 -0 ~16 !0 (total 17)
	...
```

Notes:

- `--summary-only` now still shows the group breakdown (previously it suppressed group detail).
- Use `--group-sort desc` to list the most volatile groups first.
- Increase depth (e.g. 4 or 5) to zoom further into complex areas like `study.versions.studyDesigns.activities` or `scheduleTimelines`.
- Combine with `--json` to get a machine-readable `groupSummary` object (the `changes` array is omitted when `--summary-only` is present):

```
usdm-utils diff old.json new.json --json --group-summary --group-depth 4 --summary-only > grouped.json
jq '.groupSummary' grouped.json
```

If a particular subtree dominates (e.g. thousands of biomedical concept code/value changes), raise depth to isolate which part is most active or apply `--path-filter` to narrow the analysis.
```

### CI snippet (GitHub Actions)

Fail a CI job when differences are present using `--fail-on-change`:

```bash
usdm-utils diff old.json new.json --json --fail-on-change > diff.json
# If changes exist exit code will be 1; summary still captured for inspection.
```

Minimal text gating (field-level):

```bash
usdm-utils diff old.json new.json --summary-only --fail-on-change
```

Object-level gating (ignores unchanged field churn):

```bash
usdm-utils diff old.json new.json --objects-only --summary-only --fail-on-change
```

Extract counts for PR annotation without failing:

```bash
usdm-utils diff old.json new.json --objects-only --summary-only --json > obj_summary.json
jq '.summary' obj_summary.json

The JSON `.summary` object always includes: added, removed, changed, typeMismatches, total.
### Lightweight standalone comparator (no Click)

For a fast, minimal structural comparison (simple add/remove/change/type with optional list alignment):

```bash
python bin/json_compare.py old.json new.json
```

Align lists of objects by a stable key to suppress noisy positional diffs:

```bash
python bin/json_compare.py old.json new.json --list-key id
```

Limit the verbosity of large values:

```bash
python bin/json_compare.py old.json new.json --max-list 10
```

Machine-readable JSON output:

```bash
python bin/json_compare.py old.json new.json --json > lightweight_diff.json
```

Note: This tool intentionally omits grouping, section filters, and object-level aggregation—use `usdm-utils diff` for richer reporting.

### Side-by-side HTML object diff

Generate an HTML report showing each changed object (collapsed at object level) with old vs new JSON side-by-side:

```bash
usdm-utils diff-html files/pilot_LLZT_amendment_10SEP25.json files/pilot_LLZT_amendment_11SEP25.json \
	--output output/diff_objects.html --list-key id
```

Custom object identifier precedence:

```bash
usdm-utils diff-html old.json new.json --output diff.html --object-id-key uuid --object-id-key code
```

Open the generated `diff_objects.html` in a browser to inspect changed objects with pretty-printed JSON.

### Deprecated legacy diff script

The earlier standalone normalization script `bin/usdm_diff.py` has been retired. It is now a stub that prints a deprecation message and exits with code 0.

Use the richer CLI commands instead:

```bash
usdm-utils diff old.json new.json --objects-only            # object-centric summary
usdm-utils diff-html old.json new.json --output diff.html   # HTML side-by-side
```

For lightweight structural changes (add/remove/change/type) you can still use:

```bash
python bin/json_compare.py old.json new.json --json > lightweight_diff.json
```

Rationale: The CLI supports object grouping, identifier filtering, list alignment, markdown / HTML output, and future extensibility beyond what the legacy script provided.

### Object-level mode and ID filtering

Collapse field-level noise into object additions/removals/changes:

```bash
usdm-utils diff old.json new.json --objects-only
```

Provide custom identifier keys if your objects don't use `id`/`ID`:

```bash
usdm-utils diff old.json new.json --objects-only --object-id-key uuid --object-id-key code
```

Filter the resulting object set by (substring match, case-insensitive) identifier value(s):

```bash
# Only show objects whose resolved id contains 'StudyVersion_1'
usdm-utils diff old.json new.json --objects-only --object-id-filter StudyVersion_1

# Combine multiple filters (logical OR)
usdm-utils diff old.json new.json \
	--objects-only \
	--object-id-filter StudyVersion_1 \
	--object-id-filter ARM_001
```

Emit structured JSON with the filtered objects:

```bash
usdm-utils diff old.json new.json \
	--objects-only \
	--object-id-filter StudyVersion_1 \
	--json > focused_objects.json
```

The JSON payload adds:

- `mode: "objects"`
- `idKeys`: identifier key precedence list
- `idFilters`: (when provided) the applied filter substrings

When a filter yields zero objects you will see a summary line with Total: 0 (filtered by ...). This indicates no changed/added/removed objects matched those identifier substrings (the object itself may simply be unchanged across versions).

### Summary-only mode (objects vs field level)

`--summary-only` suppresses the detailed change list while keeping aggregated counts.

Examples:

```bash
# Field-level summary
usdm-utils diff old.json new.json --summary-only

# Object-level summary (collapses field changes per object)
usdm-utils diff old.json new.json --objects-only --summary-only

# Machine-readable object-level summary
usdm-utils diff old.json new.json --objects-only --summary-only --json > summary.json
```

In JSON mode the `changes` array is empty when `--summary-only` is supplied. The `summary.total` value still reflects the number of objects (object mode) or individual field-level change records (field mode).

## CLI alternatives (without installing the package)

Use the module path if the `usdm-utils` command is not available:

```bash
python -m cdisc_usdm_utils.cli sdtm all --usdm-file files/pilot_LLZT_protocol.json --out-dir output
```

## Deprecation notice

Legacy runners under `bin/run_create_*.py` are deprecated and will exit with a message. Use the CLI instead:

- All domains: `usdm-utils sdtm all ...`
- One domain: `usdm-utils sdtm one <TA|TE|TV|TI|TS> ...`
- XPT export: `usdm-utils xpt ...`
- Define-XML: `usdm-utils define ...`

## Troubleshooting

- Command not found: `usdm-utils`
  - Ensure the package is installed: `pip install -e .` and your venv is activated.
- TS is skipped
  - Provide `spec/TSPARM_spec.csv` or remove TS from your run.
- JSON Schema errors
  - See `*.schema.errors.txt` for detailed paths/messages; fix mappings or adjust input.

## Try it

Quick smoke using the included pilot protocol:

```bash
usdm-utils sdtm all --usdm-file files/pilot_LLZT_protocol.json --out-dir output
```

Or run the portable smoke script (falls back to `python -m` if the CLI isn’t installed):

```bash
bash scripts/smoke_sdtm.sh
```

VS Code users can run the test task: “smoke: sdtm all (pilot_LLZT_protocol)” from the Run Task menu.
