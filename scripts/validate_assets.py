"""Validate required references, GLB structure, and viewer files."""

from __future__ import annotations

import csv
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_glb_json(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != b"glTF":
        raise AssertionError(f"{path} is not a GLB file")
    version, length = struct.unpack_from("<II", data, 4)
    if version != 2 or length != len(data):
        raise AssertionError(f"{path} has invalid GLB header")
    chunk_length, chunk_type = struct.unpack_from("<II", data, 12)
    if chunk_type != 0x4E4F534A:
        raise AssertionError(f"{path} does not start with a JSON chunk")
    return json.loads(data[20 : 20 + chunk_length].decode("utf-8"))


def validate_reference_index() -> list[str]:
    index_path = ROOT / "references" / "reference-index.csv"
    if not index_path.exists():
        raise AssertionError("reference-index.csv is missing")
    rows = list(csv.DictReader(index_path.read_text(encoding="utf-8-sig").splitlines()))
    if len(rows) < 7:
        raise AssertionError(f"expected at least 7 reference records, found {len(rows)}")
    for row in rows:
        for field in ("local_file", "subject", "component", "view", "source_page", "direct_url", "artist", "license", "sha256"):
            if not row.get(field):
                raise AssertionError(f"reference row missing {field}: {row}")
        if not (ROOT / "references" / row["local_file"]).exists():
            raise AssertionError(f"missing reference image: {row['local_file']}")
    return [row["local_file"] for row in rows]


def reference_ids_from_rows(rows: list[str]) -> set[str]:
    aliases = {
        "qj\\qj-2655-side-1600.jpg": "QJ-side",
        "qj\\qj-2655-three-quarter-1600.jpg": "QJ-three-quarter",
        "qj\\qj-2655-front-detail-1600.jpg": "QJ-front-detail",
        "cr400af\\cr400af-front-cc0-1600.jpg": "CR400AF-front",
        "cr400af\\cr400af-side-1600.jpg": "CR400AF-side",
        "cr400af\\cr400af-bogie-1600.jpg": "CR400AF-bogie",
        "cr400af\\cr400af-line-scan-1600.jpg": "CR400AF-line-scan",
    }
    return {aliases[path] for path in rows if path in aliases}


def validate_model(path: Path, prefix: str, required_tokens: tuple[str, ...]) -> int:
    document = read_glb_json(path)
    names = [node.get("name", "") for node in document.get("nodes", [])]
    prefix_names = [name for name in names if name.startswith(prefix)]
    if len(prefix_names) < 10:
        raise AssertionError(f"{path.name} has too few named nodes: {len(prefix_names)}")
    missing = [token for token in required_tokens if not any(token.lower() in name.lower() for name in prefix_names)]
    if missing:
        raise AssertionError(f"{path.name} is missing component groups: {', '.join(missing)}")
    return len(prefix_names)


def main() -> None:
    references = validate_reference_index()
    qj_count = validate_model(ROOT / "models" / "QJ_steam_locomotive.glb", "QJ_", ("Boiler", "Cab", "Driving_Wheel", "Axle", "Main_Rod", "Brake", "Tender", "Coupling"))
    cr_count = validate_model(ROOT / "models" / "CR400AF_emu.glb", "CR400AF_", ("Car_Body", "Window", "Bogie", "Pantograph", "Interior", "Underframe", "Coupler"))
    required_files = [
        ROOT / "models" / "model-manifest.json",
        ROOT / "viewer" / "index.html",
        ROOT / "viewer" / "app.js",
        ROOT / "video" / "storyboard.md",
        ROOT / "runs" / "README.md",
        ROOT / "runs" / "prompts" / "qj_initial.md",
        ROOT / "runs" / "prompts" / "cr400af_initial.md",
        ROOT / "scripts" / "new_astra_run.ps1",
        ROOT / "scripts" / "start_viewer.ps1",
        ROOT / "video" / "production-manifest.json",
    ]
    for file_path in required_files:
        if not file_path.exists():
            raise AssertionError(f"missing required project file: {file_path}")
    manifest = json.loads((ROOT / "models" / "model-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "procedural baseline; not an Astra run":
        raise AssertionError("baseline provenance marker is missing")
    reference_rows = list(csv.DictReader((ROOT / "references" / "reference-index.csv").read_text(encoding="utf-8-sig").splitlines()))
    allowed_reference_ids = reference_ids_from_rows([row["local_file"] for row in reference_rows])
    model_reference_ids = set()
    for subject in manifest.get("subjects", {}).values():
        for obj in subject.get("objects", []):
            model_reference_ids.update(filter(None, (item.strip() for item in obj.get("reference_ids", "").split(","))))
    unknown_ids = sorted(model_reference_ids - allowed_reference_ids - {"scene-track"})
    if unknown_ids:
        raise AssertionError(f"model references are missing from the reference archive: {', '.join(unknown_ids)}")
    print(f"PASS: {len(references)} references, {qj_count} QJ nodes, {cr_count} CR400AF nodes, viewer files present")


if __name__ == "__main__":
    main()
