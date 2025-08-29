"""Deprecated shim. Use cdisc_usdm_utils.domains.ts instead."""

import sys
import warnings
from cdisc_usdm_utils.domains.ts import generate


def _emit_deprecation_warning():
    msg = (
        "DEPRECATED: bin/create_ts_csv.py will be removed in a future release.\n"
        "Use the unified CLI instead:\n"
        "  python -m cdisc_usdm_utils.cli sdtm one --domain TS --usdm-file <USDM_JSON> --out-dir <OUT_DIR>\n"
        "  # Optional: --ts-spec-file spec/TS_spec.csv --tsparm-spec-file spec/TSPARM_spec.csv\n"
    )
    try:
        warnings.simplefilter("default", DeprecationWarning)
        warnings.warn(msg, DeprecationWarning, stacklevel=2)
    except Exception:
        pass
    try:
        print(msg, file=sys.stderr)
    except Exception:
        pass


def main(usdm_file, ts_spec_file, tsparm_spec_file, output_file):
    _emit_deprecation_warning()
    return generate(usdm_file, output_file, ts_spec_file, tsparm_spec_file)


if __name__ == "__main__":
    import argparse

    _emit_deprecation_warning()
    parser = argparse.ArgumentParser(description="Create TS dataset from USDM JSON.")
    parser.add_argument("usdm_file", help="Input USDM JSON file")
    parser.add_argument("output_file", help="Output TS CSV file")
    parser.add_argument(
        "--ts_spec_file", default="spec/TS_spec.csv", help="TS spec file"
    )
    parser.add_argument(
        "--tsparm_spec_file", default="spec/TSPARM_spec.csv", help="TSPARM spec file"
    )
    args = parser.parse_args()
    main(args.usdm_file, args.ts_spec_file, args.tsparm_spec_file, args.output_file)
