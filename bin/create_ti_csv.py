"""Deprecated shim. Use cdisc_usdm_utils.domains.ti instead."""

import sys
import warnings
from cdisc_usdm_utils.domains.ti import generate


def _emit_deprecation_warning():
    msg = (
        "DEPRECATED: bin/create_ti_csv.py will be removed in a future release.\n"
        "Use the unified CLI instead:\n"
        "  python -m cdisc_usdm_utils.cli sdtm one --domain TI --usdm-file <USDM_JSON> --out-dir <OUT_DIR>\n"
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


def main(usdm_file, output_file):
    _emit_deprecation_warning()
    return generate(usdm_file, output_file)


if __name__ == "__main__":
    import argparse

    _emit_deprecation_warning()
    parser = argparse.ArgumentParser(description="Create TI dataset from USDM JSON.")
    parser.add_argument("usdm_file", help="Input USDM JSON file")
    parser.add_argument("output_file", help="Output TI CSV file")
    args = parser.parse_args()
    main(args.usdm_file, args.output_file)
