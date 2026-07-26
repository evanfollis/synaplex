"""Create verified, byte-identical site packaging copies of the projection."""
from __future__ import annotations

import json
import shutil

from jsonschema import Draft202012Validator

from synaplex_paths import REPO_ROOT

SOURCE = REPO_ROOT / "knowledge" / "public-projection.json"
SCHEMA = REPO_ROOT / "knowledge" / "public-projection.schema.json"
TARGETS = (
    REPO_ROOT / "site" / "src" / "data" / "public-projection.json",
    REPO_ROOT / "site" / "public" / "knowledge" / "public-projection.json",
)


def prepare() -> None:
    value = json.loads(SOURCE.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(
        schema, format_checker=Draft202012Validator.FORMAT_CHECKER
    ).validate(value)
    for target in TARGETS:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE, target)
        if target.read_bytes() != SOURCE.read_bytes():
            raise RuntimeError(f"site projection copy drift: {target}")


if __name__ == "__main__":
    prepare()
    print("site projection packaging: clean")
