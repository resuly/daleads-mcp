#!/usr/bin/env python3
"""Block an MCP release when its DA provider contracts differ."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CONTRACT_NAMES = (
    "project-intelligence-v1.json",
    "focused-api-v1.json",
)


def load_contract(repo: Path, name: str) -> dict:
    path = repo.resolve() / "contracts" / name
    if not path.is_file():
        raise FileNotFoundError(f"DA provider contract missing: {path}")
    document = json.loads(path.read_text(encoding="utf-8"))
    expected = name.removesuffix(".json")
    if document.get("contract_version") != expected:
        raise ValueError(f"unexpected DA provider contract version in {path}")
    return document


def compare(provider_repo: Path, consumer_repo: Path) -> dict:
    results = []
    for name in CONTRACT_NAMES:
        provider = load_contract(provider_repo, name)
        consumer = load_contract(consumer_repo, name)
        if provider != consumer:
            raise ValueError(
                f"{name} provider/consumer contracts differ; release the "
                "coordinated DA provider contract first"
            )
        results.append({
            "contract_version": provider["contract_version"],
            "tools": sorted(provider.get("tools", {})),
        })
    return {
        "state": "ok",
        "contracts": results,
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
