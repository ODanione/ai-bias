#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Try to extract a JSON object from arbitrary text.
    Handles:
      - raw JSON
      - JSON inside ```json ... ``` or ``` ... ```
      - JSON as the first valid {...} block found by regex

    Raises ValueError if no valid JSON object can be parsed.
    """
    # 1) Try whole text
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # 2) Try code fences ```...``` (with or without language tag)
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            candidate = part.strip()
            if not candidate:
                continue

            # Remove a possible language tag on the first line (e.g. "json")
            if "\n" in candidate:
                first_line, rest = candidate.split("\n", 1)
                if first_line.strip().lower().startswith("json"):
                    candidate = rest.strip()

            try:
                obj = json.loads(candidate)
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue

    # 3) Fallback: search for a JSON object { ... } with regex
    for match in re.finditer(r"\{.*?\}", text, re.DOTALL):
        candidate = match.group(0)
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue

    raise ValueError("No valid JSON object found in text")


def collect_persons(base_dir: str) -> List[Dict[str, Any]]:
    """
    Walk one level of subdirectories in base_dir.
    Each subdirectory name = person_type.
    In each, read all .json files, extract a JSON object per file,
    and attach 'person_type' to it.
    """
    persons: List[Dict[str, Any]] = []

    if not os.path.isdir(base_dir):
        raise NotADirectoryError(f"{base_dir!r} is not a directory")

    # Iterate over immediate children of base_dir
    for entry in os.scandir(base_dir):
        if not entry.is_dir():
            continue

        person_type = entry.name
        person_dir = entry.path

        # Find all label files in this subdirectory
        for item in os.scandir(person_dir):
            if not item.is_file():
                continue
            if not item.name.lower().endswith((".json", ".txt")):
                continue

            file_path = item.path
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                data = extract_json_from_text(text)
                # Attach person_type
                data["person_type"] = person_type
                persons.append(data)
            except Exception as e:
                # You can change this to logging if you prefer
                print(f"Warning: Skipping {file_path!r}: {e}", file=sys.stderr)

    return persons


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Collect person JSON objects from .json files in one-level "
            "subdirectories and write them into statistics.json."
        )
    )
    parser.add_argument(
        "base_dir",
        help="Base directory containing person_type subdirectories",
    )
    args = parser.parse_args()

    base_dir = os.path.abspath(args.base_dir)
    persons = collect_persons(base_dir)

    output_path = os.path.join(os.getcwd(), "statistics.json")
    with open(output_path, "w", encoding="utf-8") as out_f:
        json.dump(persons, out_f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(persons)} persons to {output_path}")


if __name__ == "__main__":
    main()
