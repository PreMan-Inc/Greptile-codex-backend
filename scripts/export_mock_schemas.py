#!/usr/bin/env python3
"""Export the reusable mock API JSON Schema and test fixture catalog."""

from __future__ import annotations

import argparse
import json

from app.mock_schema_catalog import MOCK_SCHEMA_CATALOG_PATH, build_mock_schema_catalog


def rendered_document() -> str:
    return json.dumps(build_mock_schema_catalog(), indent=2, sort_keys=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing when app/data/mock_api_schemas.json is stale",
    )
    args = parser.parse_args()
    expected = rendered_document()

    if args.check:
        actual = MOCK_SCHEMA_CATALOG_PATH.read_text() if MOCK_SCHEMA_CATALOG_PATH.exists() else ""
        if actual != expected:
            raise SystemExit(
                "app/data/mock_api_schemas.json is stale; run "
                "`uv run python scripts/export_mock_schemas.py`"
            )
        print("PASS: mock_api_schemas.json matches the Pydantic models and seed fixtures")
        return

    MOCK_SCHEMA_CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    MOCK_SCHEMA_CATALOG_PATH.write_text(expected)
    print(f"Wrote {MOCK_SCHEMA_CATALOG_PATH}")


if __name__ == "__main__":
    main()
