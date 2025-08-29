from __future__ import annotations

from typing import List, Tuple
import json
import os

try:
    from jsonschema import Draft7Validator
except Exception:  # jsonschema may not be installed yet
    Draft7Validator = None  # type: ignore


def validate_dataset_json(
    dataset: dict, expected_name: str, expected_columns: List[str]
) -> Tuple[bool, List[str]]:
    problems: List[str] = []

    # Version
    version = dataset.get("datasetJSONVersion")
    if version != "1.1":
        problems.append(f"datasetJSONVersion should be '1.1' but is {version!r}")

    # Name and OID
    name = dataset.get("name")
    if name != expected_name:
        problems.append(f"name should be {expected_name!r} but is {name!r}")
    item_group_oid = dataset.get("itemGroupOID", "") or ""
    if not item_group_oid.startswith(f"IG.{expected_name}"):
        problems.append(
            f"itemGroupOID should start with 'IG.{expected_name}' but is {item_group_oid!r}"
        )

    # Columns
    cols = dataset.get("columns")
    if not isinstance(cols, list) or not cols:
        problems.append("columns must be a non-empty list")
        return False, problems
    col_names: List[str] = []
    for c in cols:
        if isinstance(c, dict):
            n = c.get("name")
        else:
            n = str(c)
        col_names.append(n)
    if col_names != expected_columns:
        problems.append(
            "columns mismatch: expected "
            + ",".join(expected_columns)
            + " got "
            + ",".join(col_names)
        )

    # Rows and records
    rows = dataset.get("rows")
    if not isinstance(rows, list):
        problems.append("rows must be a list")
    else:
        expected_len = len(expected_columns)
        for i, r in enumerate(rows):
            if not isinstance(r, list):
                problems.append(f"row {i} must be a list")
                break
            if len(r) != expected_len:
                problems.append(
                    f"row {i} length {len(r)} != columns length {expected_len}"
                )
                break

    records = dataset.get("records")
    if isinstance(rows, list) and isinstance(records, int) and records != len(rows):
        problems.append(f"records {records} does not match number of rows {len(rows)}")

    return len(problems) == 0, problems


def write_validation_report(json_path: str, problems: List[str]):
    report_path = json_path + ".errors.txt"
    with open(report_path, "w") as f:
        for p in problems:
            f.write(p + "\n")
    return report_path


def validate_against_jsonschema(
    dataset: dict, schema_path: str
) -> Tuple[bool, List[str]]:
    problems: List[str] = []
    if Draft7Validator is None:
        return False, [
            "jsonschema not installed. Add 'jsonschema' to requirements and install to enable schema validation."
        ]
    if not os.path.exists(schema_path):
        return False, [f"Schema file not found: {schema_path}"]
    try:
        with open(schema_path) as f:
            schema = json.load(f)
    except Exception as e:
        return False, [f"Failed to load schema: {e}"]
    try:
        validator = Draft7Validator(schema)
        errs = sorted(validator.iter_errors(dataset), key=lambda e: e.path)
        if not errs:
            return True, []
        for e in errs:
            loc = "/".join([str(p) for p in e.path]) or "<root>"
            problems.append(f"{loc}: {e.message}")
        return False, problems
    except Exception as e:
        return False, [f"Validation runtime error: {e}"]


def get_dataset_schema_path() -> str:
    """
    Return the default path to the Dataset-JSON v1.1 schema used for validation.

    Centralizing this avoids duplicating the literal 'files/dataset.schema.json'
    across modules and makes future changes trivial.
    """
    return os.path.join("files", "dataset.schema.json")
