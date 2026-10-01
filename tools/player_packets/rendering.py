"""Render player-packet and relationship-map artifacts from parsed sources."""

from __future__ import annotations

import html
import math
from collections import Counter
from pathlib import Path

from .source import (
    GENERATED_BY,
    PLAYER_PACKET_ENTITY_TEMPLATE,
    PLAYER_PACKET_TEMPLATE,
    Sheet,
    character_image_path,
    character_short_description,
    latex_to_plain,
    player_safe_character_sheet,
    player_safe_rules,
    read_text,
    render_template,
    tex_path,
)


TEMPLATE_DIRECTORY = Path(__file__).with_name("templates")


def render_artifact_template(name: str, values: dict[str, str]) -> str:
    """Render one static generated-artifact template."""

    return render_template(TEMPLATE_DIRECTORY / name, values)


def generated_readme() -> str:
    return render_artifact_template("generated_readme.template.md", {"GENERATOR_PATH": GENERATED_BY})


def character_collection_tex(root: Path, characters: list[Sheet]) -> str:
    """Render the player-safe character overview page shared by every document."""

    entries = [
        render_artifact_template(
            "character_short.template.tex",
            {
                "CHARACTER_ID": character.entity_id,
                "IMAGE_PATH": character_image_path(root, character.entity_id),
                "SHORT_DESCRIPTION": character_short_description(character),
            },
        ).strip()
        for character in characters
    ]
    return render_artifact_template(
        "character_collection.template.tex",
        {"GENERATOR_PATH": GENERATED_BY, "CHARACTER_ENTRIES": "\n".join(entries)},
    )


def render_svg(
    characters: list[Sheet],
    display_names: dict[str, str],
    pair_counts: Counter[tuple[str, str]],
) -> str:
    width, height = 1200, 900
    center_x, center_y, radius = width / 2, height / 2, 310
    coordinates: dict[str, tuple[float, float]] = {}
    for index, character in enumerate(characters):
        angle = -math.pi / 2 + (2 * math.pi * index / max(len(characters), 1))
        coordinates[character.entity_id] = (center_x + radius * math.cos(angle), center_y + radius * math.sin(angle))

    max_weight = max(pair_counts.values(), default=1)
    edge_parts: list[str] = []
    for (first, second), weight in sorted(pair_counts.items()):
        x1, y1 = coordinates[first]
        x2, y2 = coordinates[second]
        strength = weight / max_weight
        opacity = 0.18 + 0.82 * strength
        stroke_width = 1.2 + 7.0 * strength
        edge_parts.append(
            render_artifact_template(
                "relationship_edge.template.svg",
                {
                    "X1": f"{x1:.1f}",
                    "Y1": f"{y1:.1f}",
                    "X2": f"{x2:.1f}",
                    "Y2": f"{y2:.1f}",
                    "STROKE_WIDTH": f"{stroke_width:.2f}",
                    "OPACITY": f"{opacity:.2f}",
                },
            ).strip()
        )
        midpoint_x, midpoint_y = (x1 + x2) / 2, (y1 + y2) / 2
        edge_parts.append(
            render_artifact_template(
                "relationship_edge_label.template.svg",
                {"X": f"{midpoint_x:.1f}", "Y": f"{midpoint_y - 5:.1f}", "WEIGHT": str(weight)},
            ).strip()
        )

    node_parts: list[str] = []
    for character in characters:
        x, y = coordinates[character.entity_id]
        name = html.escape(latex_to_plain(display_names[character.entity_id]))
        role = html.escape(latex_to_plain(character.title))
        node_parts.append(
            render_artifact_template(
                "relationship_node.template.svg",
                {
                    "X": f"{x:.1f}",
                    "Y": f"{y:.1f}",
                    "NAME_Y": f"{y - 3:.1f}",
                    "ROLE_Y": f"{y + 19:.1f}",
                    "NAME": name,
                    "ROLE": role,
                },
            ).strip()
        )

    return render_artifact_template(
        "relationship_graph.template.svg",
        {
            "GENERATOR_PATH": GENERATED_BY,
            "WIDTH": str(width),
            "HEIGHT": str(height),
            "CENTER_X": str(center_x),
            "EDGE_PARTS": "".join(edge_parts),
            "NODE_PARTS": "".join(node_parts),
        },
    )


def render_tikz(
    characters: list[Sheet],
    display_names: dict[str, str],
    pair_counts: Counter[tuple[str, str]],
) -> str:
    """Create a PDFLaTeX-native rendering of the relationship graph."""

    width, height = 12.0, 9.0
    center_x, center_y, radius = width / 2, height / 2, 3.1
    coordinates: dict[str, tuple[float, float]] = {}
    node_names: dict[str, str] = {}
    for index, character in enumerate(characters):
        angle = -math.pi / 2 + (2 * math.pi * index / max(len(characters), 1))
        coordinates[character.entity_id] = (center_x + radius * math.cos(angle), center_y + radius * math.sin(angle))
        node_names[character.entity_id] = f"relationship-node-{index}"

    max_weight = max(pair_counts.values(), default=1)
    lines = [
        "% Generated by tools/generate_player_packets.py; do not edit.",
        "\\begin{center}",
        "\\begin{tikzpicture}[x=0.075\\linewidth,y=0.075\\linewidth]",
        "  \\path[use as bounding box] (0,0) rectangle (12,9);",
        "  \\tikzset{relationship node/.style={draw=wine, fill=white, ellipse, align=center, minimum width=1.55cm, minimum height=0.95cm, inner sep=2pt}}",
    ]
    for character in characters:
        x, y = coordinates[character.entity_id]
        name = display_names[character.entity_id]
        role = character.title
        lines.append(
            f"  \\node[relationship node] ({node_names[character.entity_id]}) at ({x:.3f},{y:.3f}) "
            f"{{\\shortstack{{{name}\\\\[-0.15em]\\scriptsize {role}}}}};"
        )
    for (first, second), weight in sorted(pair_counts.items()):
        strength = weight / max_weight
        opacity = 0.18 + 0.82 * strength
        line_width = 0.25 + 1.0 * strength
        lines.append(
            f"  \\draw[wine, opacity={opacity:.2f}, line width={line_width:.2f}pt] "
            f"({node_names[first]}) -- node[midway, fill=fog, inner sep=1pt, font=\\scriptsize\\bfseries] {{{weight}}} "
            f"({node_names[second]});"
        )
    lines.extend(["\\end{tikzpicture}", "\\end{center}", ""])
    return "\n".join(lines)


def render_dot(display_names: dict[str, str], pair_counts: Counter[tuple[str, str]]) -> str:
    max_weight = max(pair_counts.values(), default=1)
    lines = [
        "// Generated by tools/generate_player_packets.py; do not edit.",
        "graph RelationshipMap {",
        '  graph [bgcolor="#F4F1F2", overlap=false, splines=true];',
        '  node [shape=ellipse, style="filled", fillcolor="white", color="#6E2034", fontname="Helvetica"];',
        '  edge [color="#6E2034", fontname="Helvetica"];',
    ]
    for identifier, display_name in sorted(display_names.items()):
        lines.append(f'  "{identifier}" [label="{latex_to_plain(display_name).replace(chr(34), chr(39))}"];')
    for (first, second), weight in sorted(pair_counts.items()):
        penwidth = 1.2 + 7.0 * weight / max_weight
        lines.append(f'  "{first}" -- "{second}" [label="{weight}", penwidth="{penwidth:.2f}"];')
    lines.append("}")
    return "\n".join(lines) + "\n"


def render_mystery_mermaid(mysteries: list[Sheet], dependencies: list[tuple[str, str]]) -> str:
    """Create an editable Mermaid source for the mystery-resolution order."""

    node_ids = {mystery.entity_id: f"mystery_{index}" for index, mystery in enumerate(mysteries)}
    lines = [
        "%% Generated by tools/generate_player_packets.py; do not edit.",
        "flowchart LR",
        "  classDef mystery fill:#FFFFFF,stroke:#6E2034,stroke-width:2px,color:#25202A",
    ]
    for mystery in mysteries:
        label = latex_to_plain(mystery.title).replace('"', "'")
        lines.append(f'  {node_ids[mystery.entity_id]}["{label}"]')
    for before, after in dependencies:
        lines.append(f"  {node_ids[before]} --> {node_ids[after]}")
    if mysteries:
        lines.append("  class " + ",".join(node_ids[mystery.entity_id] for mystery in mysteries) + " mystery")
    return "\n".join(lines) + "\n"


def render_mystery_svg(mysteries: list[Sheet], dependencies: list[tuple[str, str]]) -> str:
    """Render a compact SVG fallback from the same dependency declarations."""

    width = 840
    node_width, node_height = 430, 66
    start_y, vertical_gap = 88, 125
    height = max(230, start_y + max(len(mysteries) - 1, 0) * vertical_gap + 120)
    center_x = width / 2
    positions = {mystery.entity_id: start_y + index * vertical_gap for index, mystery in enumerate(mysteries)}
    edge_parts: list[str] = []
    for before, after in dependencies:
        edge_parts.append(
            render_artifact_template(
                "mystery_order_edge.template.svg",
                {
                    "CENTER_X": f"{center_x:.0f}",
                    "START_Y": f"{positions[before] + node_height / 2:.0f}",
                    "END_Y": f"{positions[after] - node_height / 2:.0f}",
                },
            ).strip()
        )
    node_parts: list[str] = []
    for mystery in mysteries:
        y = positions[mystery.entity_id]
        label = html.escape(latex_to_plain(mystery.title))
        node_parts.append(
            render_artifact_template(
                "mystery_order_node.template.svg",
                {
                    "X": f"{center_x - node_width / 2:.0f}",
                    "Y": f"{y - node_height / 2:.0f}",
                    "WIDTH": str(node_width),
                    "HEIGHT": str(node_height),
                    "CENTER_X": f"{center_x:.0f}",
                    "LABEL_Y": f"{y + 6:.0f}",
                    "LABEL": label,
                },
            ).strip()
        )
    return render_artifact_template(
        "mystery_order_graph.template.svg",
        {
            "GENERATOR_PATH": GENERATED_BY,
            "WIDTH": str(width),
            "HEIGHT": str(height),
            "EDGE_PARTS": "".join(edge_parts),
            "NODE_PARTS": "".join(node_parts),
        },
    )


def render_mystery_tikz(mysteries: list[Sheet], dependencies: list[tuple[str, str]]) -> str:
    """Create the PDFLaTeX-native version of the mystery-order graph."""

    node_names = {mystery.entity_id: f"mystery-order-node-{index}" for index, mystery in enumerate(mysteries)}
    lines = [
        "% Generated by tools/generate_player_packets.py; do not edit.",
        "\\begin{center}",
        "\\begin{tikzpicture}",
        f"  \\path[use as bounding box] (-3.3,{-2.0 * max(len(mysteries) - 1, 0) - 0.8:.1f}) rectangle (3.3,0.8);",
        "  \\tikzset{mystery order node/.style={draw=wine, fill=white, rounded corners=7pt, align=center, text width=4.7cm, minimum height=0.9cm, inner sep=5pt}}",
    ]
    for index, mystery in enumerate(mysteries):
        lines.append(f"  \\node[mystery order node] ({node_names[mystery.entity_id]}) at (0,{-2.0 * index:.1f}) {{{mystery.title}}};")
    for before, after in dependencies:
        lines.append(f"  \\draw[->, wine, thick] ({node_names[before]}) -- ({node_names[after]});")
    lines.extend(["\\end{tikzpicture}", "\\end{center}", ""])
    return "\n".join(lines)


def packet_tex(
    root: Path,
    character: Sheet,
    characters: list[Sheet],
    spaces: list[Sheet],
    clues: list[Sheet],
    mysteries: list[Sheet],
    character_collection: str,
) -> str:
    """Create a standalone snapshot with public rules and one sheet."""

    entity_template = root / PLAYER_PACKET_ENTITY_TEMPLATE
    declarations: list[str] = []
    for kind, sheets in (("character", characters), ("space", spaces), ("clue", clues), ("mystery", mysteries)):
        for sheet in sheets:
            declarations.append(
                render_template(
                    entity_template,
                    {"ENTITY_KIND": kind, "ENTITY_ID": sheet.entity_id, "ENTITY_TITLE": sheet.title},
                ).strip()
            )

    return render_template(
        root / PLAYER_PACKET_TEMPLATE,
        {
            "GENERATOR_PATH": GENERATED_BY,
            "SOURCE_PATH": tex_path(character.source.relative_to(root)),
            "CHARACTER_ID": character.entity_id,
            "PREAMBLE": read_text(root / "layout/preamble.tex").strip(),
            "CONFIGURED_NAMES": read_text(root / "config/characters.tex").strip(),
            "GAME_CONFIG": read_text(root / "config/game.tex").strip(),
            "ENTITY_DECLARATIONS": "\n".join(declarations),
            "PUBLIC_RULES": player_safe_rules(root),
            "CHARACTER_COLLECTION": character_collection,
            "CHARACTER_SHEET": player_safe_character_sheet(character),
        },
    )
