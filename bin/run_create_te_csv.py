import argparse
from create_te_csv import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create TE.CSV from USDM JSON file.")
    parser.add_argument(
        "--usdm_file",
        type=str,
        required=True,
        help="Path to USDM JSON file",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="output/TE.CSV",
        help="Path to output TE.CSV file",
    )
    args = parser.parse_args()
    main(args.usdm_file, args.output_file)
