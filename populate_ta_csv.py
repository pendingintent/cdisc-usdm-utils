import csv
import json
import os
from typing import Any

def extract_json_value(data: Any, path: str):
    """
    Extract value from nested JSON using a custom path syntax like:
    Study/@versions/StudyVersion/@studyIdentifiers/StudyIdentifier/@studyIdentifier
    """
    if not path:
        return None
    # Only use the first path if there are multiple separated by |
    path = path.split('|')[0].strip()
    # Split path by / and remove empty parts
    parts = [p for p in path.split('/') if p]
    current = data
    for part in parts:
        # Remove @ and normalize to lowercase for matching
        part = part.lstrip('@').strip().lower()
        # Try to match key in current dict (case-insensitive)
        if isinstance(current, dict):
            # Find key ignoring case
            key = next((k for k in current if k.lower() == part), None)
            if key is not None:
                current = current[key]
            else:
                return None
        elif isinstance(current, list):
            # If current is a list, try to get the first element
            if current:
                current = current[0]
            else:
                return None
        else:
            return None
    # If the result is a dict with a 'text' field, return that
    if isinstance(current, dict) and 'text' in current:
        return current['text']
    return current

def main():
    ta_defn_path = os.path.join('spec', 'TA_defn.csv')
    json_path = os.path.join('files', 'usdm_sdw_v4.0.0_amendment.json')
    output_path = 'TA.csv'

    # Read JSON data
    with open(json_path, 'r', encoding='utf-8') as jf:
        json_data = json.load(jf)

    # Read TA_defn.csv
    with open(ta_defn_path, 'r', encoding='utf-8-sig') as cf:
        reader = csv.DictReader(cf)
        rows = list(reader)
        fieldnames = reader.fieldnames if reader.fieldnames else []

    # Prepare output fieldnames
    output_fieldnames = fieldnames + ['Extracted Value']

    # Process each row
    output_rows = []
    for row in rows:
        # Remove any None keys (caused by extra columns or missing fields)
        if None in row:
            del row[None]
        usdm_path = row.get('USDM Path and Attribute', '').strip()
        value = extract_json_value(json_data, usdm_path) if usdm_path else None
        # If value is still None, try to print debug info
        if value is None and usdm_path:
            print(f"[DEBUG] Could not extract value for path: {usdm_path}")
        row['Extracted Value'] = value
        output_rows.append(row)

    # Write output CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as out_csv:
        writer = csv.DictWriter(out_csv, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

if __name__ == '__main__':
    main()
