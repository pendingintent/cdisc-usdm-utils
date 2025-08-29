import sys

if __name__ == "__main__":
    print(
        "[DEPRECATED] This runner has been retired. SDTM tasks are available via the CLI: usdm-utils sdtm ...; Biomedical Concepts will be exposed via the CLI in a future update.",
        file=sys.stderr,
    )
    sys.exit(1)
