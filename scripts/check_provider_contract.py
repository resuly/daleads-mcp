#!/usr/bin/env python3
"""Block an MCP release when its focused API contract differs from DA Leads."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CONTRACT_NAME = "focused-api-v1.json"


def load_contract(repo: Path) -> dict:
    path = repo.resolve() / "contracts" / CONTRACT_NAME
    if not path.is_file():
        raise FileNotFoundError(f"focused API contract missing: {path}")
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("contract_version") != "focused-api-v1":
        raise ValueError(f"unexpected focused API contract version in {path}")
    return document


def compare(provider_repo: Path, consumer_repo: Path) -> dict:
    provider = load_contract(provider_repo)
    consumer = load_contract(consumer_repo)
    if provider != consumer:
        raise ValueError(
            "focused-api-v1 provider/consumer contracts differ; release the "
            "coordinated DA provider contract first"
        )
    return {
        "state": "ok",
        "contract_version": provider["contract_version"],
        "tools": sorted(provider["tools"]),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider-repo", type=Path, required=True)
    parser.add_argument(
        "--consumer-repo",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args(argv)
    print(json.dumps(
        compare(args.provider_repo, args.consumer_repo), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
