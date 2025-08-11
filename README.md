# cdisc-usdm-utils
This repo holds utilities relating to USDM activities

## Running the Domain Extraction Scripts

All scripts are located in the `bin/` directory and can be run from the command line. By default, they use the provided USDM JSON and output to the `output/` directory.

### TA Domain
```
python bin/run_create_ta_csv.py --usdm_file files/usdm_sdw_v4.0.0_amendment.json --output_file output/TA.CSV
```

### TE Domain
```
python bin/run_create_te_csv.py --usdm_file files/usdm_sdw_v4.0.0_amendment.json --output_file output/TE.CSV
```

### TV Domain
```
python bin/run_create_tv_csv.py --usdm_file files/usdm_sdw_v4.0.0_amendment.json --output_file output/TV.CSV
```

You can override the input or output file paths using the `--usdm_file` and `--output_file` arguments.
