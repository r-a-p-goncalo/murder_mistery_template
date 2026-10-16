#!/usr/bin/env python3
"""Compile the game and collect player PDFs under person-based filenames."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

from tools.player_packets.paths import CHARACTER_CONFIG_PATH, CHARACTER_INDEX_PATH
from tools.player_packets.source import (
    PLAYER_PACKET_VARIANTS,
    SourceError,
    latex_to_plain,
    parse_configured_names,
    parse_sheets,
    source_path,
    validate_language,
)


DEFAULT_ROOT = Path(__file__).resolve().parent
ORGANIZED_DIRECTORY = Path("target/organized_characters")
MANIFEST_NAME = ".compile_and_organize_manifest.json"
GENERATED_BY = Path(__file__).name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="repository root")
    parser.add_argument("--language", default="en", help="language pack to compile (default: en)")
    parser.add_argument("--latexmk", default="latexmk", help="LaTeX build command (default: latexmk)")
    parser.add_argument(
        "--strict-language",
        action="store_true",
        help="require every path listed in the selected language manifest",
    )
    return parser.parse_args()


def person_filename_stem(configured_name: str) -> str:
    """Convert a configured person's display name to a portable filename stem."""

    plain_name = latex_to_plain(configured_name)
    decomposed = unicodedata.normalize("NFKD", plain_name)
    ascii_name = "".join(character for character in decomposed if not unicodedata.combining(character))
    stem = re.sub(r"[^a-z0-9]+", "_", ascii_name.casefold()).strip("_")
    if not stem:
        raise SourceError(f"Person name cannot be converted to a filename: {configured_name!r}")
    return stem


def run_compile(root: Path, language: str, latexmk: str, strict_language: bool) -> int:
    command = [
        sys.executable,
        str(root / "compile.py"),
        "--root",
        str(root),
        "--language",
        language,
        "--latexmk",
        latexmk,
    ]
    if strict_language:
        command.append("--strict-language")
    print(f"Running compiler for language '{language}'...")
    return subprocess.run(command, cwd=root, check=False).returncode


def load_previous_manifest(manifest_path: Path) -> set[str]:
    if not manifest_path.exists():
        return set()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise SourceError(f"Could not read organized-output manifest: {manifest_path}") from error
    if manifest.get("generated_by") != GENERATED_BY or not isinstance(manifest.get("files"), list):
        raise SourceError(f"Refusing to replace an unrecognized manifest: {manifest_path}")
    filenames = set()
    for value in manifest["files"]:
        if not isinstance(value, str) or Path(value).name != value or not value.endswith(".pdf"):
            raise SourceError(f"Invalid filename in organized-output manifest: {value!r}")
        filenames.add(value)
    return filenames


def organize_player_pdfs(root: Path, language: str) -> list[Path]:
    characters = parse_sheets(root, CHARACTER_INDEX_PATH, "CharacterSheet", language=language)
    configured_names = parse_configured_names(source_path(root, CHARACTER_CONFIG_PATH, language))
    missing_names = sorted(character.entity_id for character in characters if character.entity_id not in configured_names)
    if missing_names:
        raise SourceError(
            "Cannot organize by person name; configured player names are missing for: "
            + ", ".join(missing_names)
        )

    source_directory = root / "target" / "players" / language
    organized_directory = root / ORGANIZED_DIRECTORY
    manifest_path = organized_directory / MANIFEST_NAME
    planned: list[tuple[Path, str]] = []
    destination_names: dict[str, str] = {}
    for character in characters:
        person_stem = person_filename_stem(configured_names[character.entity_id])
        for variant, *_ in PLAYER_PACKET_VARIANTS:
            source = source_directory / character.entity_id / f"player_packet_{variant}.pdf"
            destination_name = f"{person_stem}_{variant}.pdf"
            previous_owner = destination_names.get(destination_name)
            if previous_owner is not None:
                raise SourceError(
                    f"Person-based filename collision for '{destination_name}': "
                    f"{previous_owner} and {character.entity_id}"
                )
            if not source.is_file():
                raise SourceError(f"Compiled player PDF does not exist: {source}")
            destination_names[destination_name] = character.entity_id
            planned.append((source, destination_name))

    organized_directory.mkdir(parents=True, exist_ok=True)
    previous_files = load_previous_manifest(manifest_path)
    for _, destination_name in planned:
        destination = organized_directory / destination_name
        if destination.exists() and destination_name not in previous_files:
            raise SourceError(f"Refusing to replace a file not owned by this script: {destination}")

    target_directory = root / "target"
    with tempfile.TemporaryDirectory(prefix=".organized_characters_", dir=target_directory) as staging_name:
        staging_directory = Path(staging_name)
        for source, destination_name in planned:
            shutil.copy2(source, staging_directory / destination_name)

        for filename in previous_files:
            previous_path = organized_directory / filename
            if previous_path.is_file():
                previous_path.unlink()
        for _, destination_name in planned:
            shutil.copy2(staging_directory / destination_name, organized_directory / destination_name)

    manifest = {
        "generated_by": GENERATED_BY,
        "language": language,
        "files": [destination_name for _, destination_name in planned],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return [organized_directory / destination_name for _, destination_name in planned]


def main() -> int:
    arguments = parse_args()
    root = arguments.root.resolve()
    try:
        language = validate_language(arguments.language)
    except SourceError as error:
        print(f"Organization failed: {error}", file=sys.stderr)
        return 1

    compile_result = run_compile(root, language, arguments.latexmk, arguments.strict_language)
    if compile_result != 0:
        print("Organization skipped because compilation failed.", file=sys.stderr)
        return compile_result

    try:
        organized_files = organize_player_pdfs(root, language)
    except SourceError as error:
        print(f"Organization failed: {error}", file=sys.stderr)
        return 1

    print(f"Organized {len(organized_files)} player PDFs in {root / ORGANIZED_DIRECTORY}")
    for path in organized_files:
        print(f"  {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
