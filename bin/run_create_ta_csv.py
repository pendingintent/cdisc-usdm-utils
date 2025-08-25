import argparse
from create_ta_csv import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate TA.CSV from USDM JSON.")
    parser.add_argument(
        "--usdm_file", type=str, required=True, help="Path to the USDM JSON file."
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="output/TA.CSV",
        help="Path to the output TA.CSV file.",
    )
    args = parser.parse_args()
    main(args.usdm_file, args.output_file)
