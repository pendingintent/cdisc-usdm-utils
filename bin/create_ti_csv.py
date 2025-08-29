"""Deprecated shim. Use cdisc_usdm_utils.domains.ti instead."""

from cdisc_usdm_utils.domains.ti import generate


def main(usdm_file, output_file):
    print(
        "[DEPRECATED] bin/create_ti_csv.py is now a thin wrapper. Use the CLI or domains.ti module."
    )
    return generate(usdm_file, output_file)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create TI dataset from USDM JSON.")
    parser.add_argument("usdm_file", help="Input USDM JSON file")
    parser.add_argument("output_file", help="Output TI CSV file")
    args = parser.parse_args()
    main(args.usdm_file, args.output_file)
