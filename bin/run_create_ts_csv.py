import sys

if __name__ == "__main__":
    print(
        "[DEPRECATED] Use the CLI instead: usdm-utils sdtm one TS --usdm-file <USDM.json> --out-dir output",
        file=sys.stderr,
    )
    sys.exit(1)
