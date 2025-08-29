# cdisc-usdm-utils
This repo holds utilities relating to USDM activities
# cdisc-usdm-utils
[![Smoke SDTM](https://github.com/pendingintent/cdisc-usdm-utils/actions/workflows/smoke.yml/badge.svg)](https://github.com/pendingintent/cdisc-usdm-utils/actions/workflows/smoke.yml)
Utilities to generate SDTM domain outputs (CSV + Dataset-JSON v1.1), Define-XML, and XPT files from USDM.

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
