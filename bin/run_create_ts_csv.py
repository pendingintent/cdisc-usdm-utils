import argparse
from create_ts_csv import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TS dataset creation from USDM JSON.")
    parser.add_argument("--usdm_file", required=False, help="Input USDM JSON file")
    parser.add_argument("--output_file", required=False, help="Output TS CSV file")
    parser.add_argument("--ts_spec_file", default="spec/TS_spec.csv", help="TS spec file")
    parser.add_argument("--tsparm_spec_file", default="spec/TSPARM_spec.csv", help="TSPARM spec file")
    parser.add_argument("usdm_file_pos", nargs="?", help="Input USDM JSON file (positional, optional)")
    parser.add_argument("output_file_pos", nargs="?", help="Output TS CSV file (positional, optional)")
    args = parser.parse_args()

    # Prefer --usdm_file/--output_file, fallback to positional
    usdm_file = args.usdm_file or args.usdm_file_pos
    output_file = args.output_file or args.output_file_pos
    if not usdm_file or not output_file:
        parser.error("You must provide both --usdm_file and --output_file (or positional equivalents).")
    main(usdm_file, args.ts_spec_file, args.tsparm_spec_file, output_file)
