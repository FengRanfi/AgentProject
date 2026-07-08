#!/usr/bin/env python3
"""Download search-agent datasets from Hugging Face Hub."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


DATASETS = [
    "PolarSeeker/OpenSeeker-v1-Data",
    "OpenResearcher/OpenResearcher-Dataset",
    "McGill-NLP/WebLINX",
]

DEFAULT_TARGET = Path(
    "/home/flf/Project/AgentProject/AgentProject/dataset/searchAgent/direct"
)


def import_snapshot_download():
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print(
            "Missing dependency: huggingface_hub\n"
            "Install it with: python3 -m pip install -U huggingface_hub",
            file=sys.stderr,
        )
        raise SystemExit(1)

    return snapshot_download


def dataset_dir(repo_id: str) -> str:
    return repo_id.replace("/", "__")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download selected search-agent datasets to a local directory."
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=DEFAULT_TARGET,
        help=f"Download destination. Default: {DEFAULT_TARGET}",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Optional Hugging Face token. Usually not needed for these public datasets.",
    )
    parser.add_argument(
        "--dataset",
        action="append",
        choices=DATASETS,
        help="Download only one dataset. Can be passed multiple times.",
    )
    args = parser.parse_args()

    snapshot_download = import_snapshot_download()
    repos = args.dataset or DATASETS
    args.target_dir.mkdir(parents=True, exist_ok=True)

    print(f"Target directory: {args.target_dir}")
    for repo_id in repos:
        local_dir = args.target_dir / dataset_dir(repo_id)
        local_dir.mkdir(parents=True, exist_ok=True)
        print(f"\nDownloading {repo_id} -> {local_dir}")
        snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            local_dir=str(local_dir),
            token=args.token,
        )
        print(f"Done: {repo_id}")

    print("\nAll requested datasets downloaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
