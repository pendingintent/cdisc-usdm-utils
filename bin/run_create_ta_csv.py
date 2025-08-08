
import argparse
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from create_ta_csv import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate TA.CSV from USDM JSON.")
    parser.add_argument('--usdm_file', required=True, help='Path to the input USDM JSON file.')
    parser.add_argument('--out_file', required=True, help='Path to the output TA.CSV file.')
    args = parser.parse_args()
    main(args.usdm_file, args.out_file)
