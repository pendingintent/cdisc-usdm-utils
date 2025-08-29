import pandas as pd
import pyreadstat
from pathlib import Path


def write_xpt_for_domains(domains, csv_dir: str, out_dir: str):
    csv_dir_p = Path(csv_dir)
    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)

    labels_map = {
        "TA": "Trial Arms",
        "TE": "Trial Elements",
        "TV": "Trial Visits",
        "TI": "Trial Inclusion/Exclusion",
        "TS": "Trial Summary",
    }

    for dom in domains:
        csv_path = csv_dir_p / f"{dom}.csv"
        if not csv_path.exists():
            continue
        df = pd.read_csv(csv_path)
        # Optional: enforce <= 8 char variable names for v5 compatibility
        df.columns = [c[:8] for c in df.columns]
        xpt_path = out_dir_p / f"{dom}.xpt"
        pyreadstat.write_xport(
            df,
            str(xpt_path),
            file_label=labels_map.get(dom, dom),
            column_labels=[c for c in df.columns],
        )


if __name__ == "__main__":
    # Ad-hoc run writing all domains from output/ to output/
    write_xpt_for_domains(["TA", "TE", "TV", "TI", "TS"], "output", "output")
