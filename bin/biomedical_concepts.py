import json
from typing import List, Dict, Any, Optional, Iterable, Tuple
import pandas as pd


def _extract_standard_code(obj: Dict[str, Any]) -> Tuple[str, str]:
    if not isinstance(obj, dict):
        return "", ""
    code_block = obj.get("code") or {}
    std = code_block.get("standardCode") if isinstance(code_block, dict) else None
    if isinstance(std, dict):
        return std.get("code", ""), std.get("decode", "")
    # Some response code structures may flatten
    return code_block.get("code", ""), code_block.get("decode", "")


def load_usdm(usdm_file: str) -> Dict[str, Any]:
    with open(usdm_file, "r", encoding="utf-8") as f:
        return json.load(f)


def iterate_concepts(version: Dict[str, Any], include_surrogates: bool = True) -> Iterable[Dict[str, Any]]:
    for bc in version.get("biomedicalConcepts", []) or []:
        yield bc
    if include_surrogates:
        for s in version.get("bcSurrogates", []) or []:
            yield s


def build_rows(
    version: Dict[str, Any],
    *,
    include_surrogates: bool = True,
    include_response_codes: bool = True,
    filter_name: Optional[str] = None,
    filter_reference_prefix: Optional[str] = None,
    filter_code_system: Optional[str] = None,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    concepts = list(iterate_concepts(version, include_surrogates=include_surrogates))
    name_sub = filter_name.lower() if filter_name else None
    ref_pref = filter_reference_prefix
    code_sys = filter_code_system.lower() if filter_code_system else None

    def name_matches(n: str) -> bool:
        return True if not name_sub else (n or "").lower().find(name_sub) >= 0

    def ref_matches(r: str) -> bool:
        return True if not ref_pref else (r or "").startswith(ref_pref)

    def code_system_matches(obj: Dict[str, Any]) -> bool:
        if not code_sys:
            return True
        code_block = obj.get("code") or {}
        std = code_block.get("standardCode") if isinstance(code_block, dict) else None
        system = ""
        if isinstance(std, dict):
            system = std.get("codeSystem") or std.get("system") or ""
        else:
            system = code_block.get("codeSystem") or code_block.get("system") or ""
        return (system or "").lower() == code_sys

    for bc in concepts:
        if not name_matches(bc.get("name", "")):
            continue
        if not ref_matches(bc.get("reference", "")):
            continue
        if not code_system_matches(bc):
            continue
        bcode, bdecode = _extract_standard_code(bc)
        rows.append(
            {
                "id": bc.get("id", ""),
                "parent_id": "",
                "name": bc.get("name", ""),
                "label": bc.get("label", ""),
                "synonyms": ", ".join(bc.get("synonyms", []) or []),
                "reference": bc.get("reference", ""),
                "code": bcode,
                "decode": bdecode,
                "type": bc.get("instanceType", "BiomedicalConcept"),
            }
        )
        # properties
        for prop in bc.get("properties", []) or []:
            pcode, pdecode = _extract_standard_code(prop)
            rows.append(
                {
                    "id": prop.get("id", ""),
                    "parent_id": bc.get("id", ""),
                    "name": prop.get("name", ""),
                    "label": prop.get("label", ""),
                    "synonyms": "",
                    "reference": prop.get("reference", ""),
                    "code": pcode,
                    "decode": pdecode,
                    "type": prop.get("instanceType", "BiomedicalConceptProperty"),
                }
            )
            if include_response_codes:
                for rc in prop.get("responseCodes", []) or []:
                    rccode, rcdecode = _extract_standard_code(rc)
                    rows.append(
                        {
                            "id": rc.get("id", ""),
                            "parent_id": prop.get("id", ""),
                            "name": rc.get("name", ""),
                            "label": rc.get("label", ""),
                            "synonyms": "",
                            "reference": "",
                            "code": rccode,
                            "decode": rcdecode,
                            "type": rc.get("instanceType", "ResponseCode"),
                        }
                    )
    return rows


def process_usdm_biomedical_concepts_to_csv(
    usdm_file: str,
    out_file: str,
    *,
    include_surrogates: bool = True,
    include_response_codes: bool = True,
    filter_name: Optional[str] = None,
    filter_reference_prefix: Optional[str] = None,
    filter_code_system: Optional[str] = None,
):
    """Process a USDM JSON file and output biomedical concepts to a CSV file (configurable)."""
    try:
        usdm = load_usdm(usdm_file)
    except FileNotFoundError:
        print(f"The input JSON file {usdm_file} does not exist")
        return
    version = usdm.get("study", {}).get("versions", [])[0]
    rows = build_rows(
        version,
        include_surrogates=include_surrogates,
        include_response_codes=include_response_codes,
        filter_name=filter_name,
        filter_reference_prefix=filter_reference_prefix,
        filter_code_system=filter_code_system,
    )
    if not rows:
        pd.DataFrame(
            columns=[
                "id",
                "parent_id",
                "name",
                "label",
                "synonyms",
                "reference",
                "code",
                "decode",
                "type",
            ]
        ).to_csv(out_file, index=False)
        return
    df = pd.DataFrame(rows)
    df = df[["id", "parent_id", "name", "label", "synonyms", "reference", "code", "decode", "type"]]
    df.to_csv(out_file, index=False)


def concepts_to_json(
    usdm_file: str,
    *,
    include_surrogates: bool = True,
    include_response_codes: bool = True,
    filter_name: Optional[str] = None,
    filter_reference_prefix: Optional[str] = None,
    filter_code_system: Optional[str] = None,
) -> List[Dict[str, Any]]:
    usdm = load_usdm(usdm_file)
    version = usdm.get("study", {}).get("versions", [])[0]
    return build_rows(
        version,
        include_surrogates=include_surrogates,
        include_response_codes=include_response_codes,
        filter_name=filter_name,
        filter_reference_prefix=filter_reference_prefix,
        filter_code_system=filter_code_system,
    )


def concepts_markdown_tree(rows: List[Dict[str, Any]]) -> str:
    """Render a lineage tree (Concept -> Property -> ResponseCode) as markdown."""
    # Build lookup
    by_id = {r["id"]: r for r in rows}
    children: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        pid = r.get("parent_id")
        if pid:
            children.setdefault(pid, []).append(r)
    # Sort children for stable output
    for lst in children.values():
        lst.sort(key=lambda x: (x.get("type"), x.get("name")))
    # Top-level nodes
    tops = [r for r in rows if not r.get("parent_id")]
    tops.sort(key=lambda x: (x.get("type"), x.get("name")))

    lines: List[str] = ["# Biomedical Concepts Lineage", ""]
    def emit(node: Dict[str, Any], depth: int = 0):
        indent = "  " * depth
        label = node.get("name") or node.get("id")
        t = node.get("type", "")
        code = node.get("code")
        code_part = f" (code: {code})" if code else ""
        lines.append(f"{indent}- **{label}** *{t}*{code_part}")
        for ch in children.get(node.get("id"), []):
            emit(ch, depth + 1)
    for top in tops:
        emit(top, 0)
    return "\n".join(lines)


# Backwards compatibility: retain original simple signature
# (deprecated path – new features require extended call site.)
