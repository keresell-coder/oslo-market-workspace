#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from build_static_site_data import INPUT_DIR, SchemaError, load_inputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Oslo Stock static YAML inputs without generating public JSON."
    )
    parser.add_argument("--input-dir", type=Path, default=INPUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    inputs = load_inputs(args.input_dir)
    watchlist_count = len(inputs["watchlist"]["items"])
    peer_group_count = len(inputs["peer_groups"])
    peer_item_count = sum(len(group["items"]) for group in inputs["peer_groups"])
    print(
        f"Validated static inputs: {watchlist_count} watchlist rows, "
        f"{peer_group_count} peer groups, {peer_item_count} peer rows."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SchemaError as exc:
        print(f"Schema error: {exc}")
        raise SystemExit(2)
