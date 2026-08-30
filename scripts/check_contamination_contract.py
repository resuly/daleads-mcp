"""Fail an MCP release when the private provider contract drifts."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


CONTRACT_PATH = Path("contracts/contamination-screening-v1.json")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(provider_repo: Path, consumer_repo: Path) -> dict:
    provider = provider_repo / CONTRACT_PATH
    consumer = consumer_repo / CONTRACT_PATH
    if not provider.is_file():
        raise ValueError(f"provider contract missing: {provider}")
    if not consumer.is_file():
        raise ValueError(f"consumer contract missing: {consumer}")
    provider_hash = _sha256(provider)
    consumer_hash = _sha256(consumer)
    if provider_hash != consumer_hash:
        raise ValueError(
            "provider/consumer contamination contracts differ: "
            f"{provider_hash} != {consumer_hash}")
    return {"state": "ok", "sha256": provider_hash}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider-repo", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.provider_repo.resolve(), Path.cwd().resolve())
    print(f"Contamination provider/MCP contract: {result['state']} {result['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
