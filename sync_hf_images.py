#!/usr/bin/env python3
"""Sync local public AI-generated image folders to Hugging Face.

Local layout:
  images/FLUX/

Hugging Face dataset layout:
  FLUX/

Reference folders such as images/AdobeStock and images/GoogleSearch are
intentionally excluded from this sync.
"""

import argparse
from pathlib import Path

from huggingface_hub import HfApi

from image_paths import IMAGE_ROOT, PUBLIC_DATASET_SOURCES

DEFAULT_REPO_ID = "ODanione/ai-bias-images"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload public AI-generated image folders to Hugging Face."
    )
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID)
    parser.add_argument(
        "--source",
        action="append",
        choices=PUBLIC_DATASET_SOURCES,
        help="Source folder to sync. Can be repeated. Defaults to all public sources.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the local-to-remote mapping without uploading.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sources = args.source or list(PUBLIC_DATASET_SOURCES)

    api = HfApi()
    for source in sources:
        folder = IMAGE_ROOT / source
        if not folder.is_dir():
            print(f"Skipping missing local folder: {folder}")
            continue

        print(f"{folder} -> {args.repo_id}:{source}/")
        if args.dry_run:
            continue

        info = api.upload_folder(
            repo_id=args.repo_id,
            repo_type="dataset",
            folder_path=folder,
            path_in_repo=source,
            commit_message=f"Sync local images/{source} folder",
            commit_description=(
                "Upload from the local images/ layout while preserving the "
                "root-level source-folder layout in the Hugging Face dataset."
            ),
        )
        print(info.commit_url)


if __name__ == "__main__":
    main()
