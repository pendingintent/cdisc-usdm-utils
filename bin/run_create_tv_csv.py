import argparse
from create_tv_csv import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create TV.CSV from USDM JSON file.")
    parser.add_argument(
        "--usdm_file",
        type=str,
        required=True,
        help="Path to USDM JSON file",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="output/TV.CSV",
        help="Path to output TV.CSV file",
    )
    args = parser.parse_args()
    main(args.usdm_file, args.output_file)
