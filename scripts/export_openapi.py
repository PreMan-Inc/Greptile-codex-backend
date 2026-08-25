#!/usr/bin/env python3
"""Export the exact API contract consumed by repository-based agents."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.main import app

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "openapi.json"


def rendered_document() -> str:
    return json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing when docs/openapi.json is stale",
    )
    args = parser.parse_args()
    expected = rendered_document()

    if args.check:
        actual = OUTPUT.read_text() if OUTPUT.exists() else ""
        if actual != expected:
            raise SystemExit(
                "docs/openapi.json is stale; run `uv run python scripts/export_openapi.py`"
            )
        print("PASS: docs/openapi.json matches the application contract")
        return

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(expected)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
