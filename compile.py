#!/usr/bin/env python3
"""Build the generated game assets and the main murder-mystery PDF."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from tools.player_packets.generator import build
from tools.player_packets.source import SourceError


DEFAULT_ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="repository root (default: this file's directory)")
    parser.add_argument("--generated-dir", type=Path, default=Path("generated"), help="derived-asset directory (default: generated)")
    parser.add_argument(
        "--main-output-dir",
        "--output-dir",
        dest="main_output_dir",
        type=Path,
        default=Path("target/main"),
        help="main PDF output directory (default: target/main)",
    )
    parser.add_argument(
        "--player-output-dir",
        type=Path,
        default=Path("target/players"),
        help="player-packet PDF output directory (default: target/players)",
    )
    parser.add_argument("--latexmk", default="latexmk", help="LaTeX build command (default: latexmk)")
    return parser.parse_args()


def resolve_from(root: Path, path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def compile_document(latexmk: str, root: Path, source: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        latexmk,
        "-pdf",
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-outdir={output_dir}",
        str(source),
    ]
    try:
        return subprocess.run(command, cwd=root, check=False).returncode
    except FileNotFoundError:
        print(f"Build failed: could not find LaTeX command '{latexmk}'.", file=sys.stderr)
        return 1


def main() -> int:
    arguments = parse_args()
    root = arguments.root.resolve()
    generated_dir = resolve_from(root, arguments.generated_dir)
    main_output_dir = resolve_from(root, arguments.main_output_dir)
    player_output_dir = resolve_from(root, arguments.player_output_dir)
    main_source = root / "murder_mystery.tex"

    if not main_source.is_file():
        print(f"Build failed: main document does not exist: {main_source}", file=sys.stderr)
        return 1

    print("Generating derived game assets...")
    try:
        analysis = build(root, generated_dir)
    except SourceError as error:
        print(f"Generation failed: {error}", file=sys.stderr)
        return 1

    player_count = len(analysis["character_reference_counts"])
    print(f"Generated {player_count} player packets: {generated_dir / 'players'}")
    print(f"Relationship analysis: {generated_dir / 'relationship_analysis.json'}")
    validation = analysis["validation"]
    validation_messages = {
        "unknown_character_references_in_relationship_map": "unknown character references in the Relationship map",
        "configured_character_ids_without_sheets": "configured character IDs without sheets",
        "characters_without_configured_player_name": "characters without configured player names",
    }
    for key, description in validation_messages.items():
        details = validation[key]
        if details:
            print(f"Warning: {description}: {details}")

    print(f"Compiling {main_source.name} with {arguments.latexmk}...")
    main_result = compile_document(arguments.latexmk, root, main_source, main_output_dir)
    if main_result != 0:
        print("LaTeX compilation failed; generated assets were left in place for inspection.", file=sys.stderr)
        return main_result

    player_sources = sorted((generated_dir / "players").glob("*/player_packet.tex"))
    print(f"Compiling {len(player_sources)} player packets...")
    for index, player_source in enumerate(player_sources, start=1):
        player_id = player_source.parent.name
        print(f"  [{index}/{len(player_sources)}] {player_id}")
        player_result = compile_document(arguments.latexmk, root, player_source, player_output_dir / player_id)
        if player_result != 0:
            print(f"Player-packet compilation failed for '{player_id}'.", file=sys.stderr)
            return player_result

    pdf_path = main_output_dir / "murder_mystery.pdf"
    print("Build complete.")
    print(f"Main PDF: {pdf_path}")
    print(f"Generated assets: {generated_dir}")
    print(f"Player packet sources: {generated_dir / 'players'}")
    print(f"Player packet PDFs: {player_output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
