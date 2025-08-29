"""Deprecated shim. Use cdisc_usdm_utils.domains.ts instead."""

from cdisc_usdm_utils.domains.ts import generate


def main(usdm_file, ts_spec_file, tsparm_spec_file, output_file):
    print(
        "[DEPRECATED] bin/create_ts_csv.py is now a thin wrapper. Use the CLI or domains.ts module."
    )
    return generate(usdm_file, output_file, ts_spec_file, tsparm_spec_file)


if __name__ == "__main__":
    import argparse

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
