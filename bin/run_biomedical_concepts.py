import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from bin.biomedical_concepts import process_usdm_biomedical_concepts_to_csv

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Process USDM JSON to Biomedical Concepts CSV."
    )
    parser.add_argument(
        "--usdm_file", required=True, help="Path to the input USDM JSON file."
    )
    parser.add_argument(
        "--out_file", required=True, help="Path to the output CSV file."
    )
    args = parser.parse_args()
    process_usdm_biomedical_concepts_to_csv(args.usdm_file, args.out_file)
