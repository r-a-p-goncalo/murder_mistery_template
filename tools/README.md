# Dynamic player packets

Run the complete build from the repository root after changing `content/`, `config/`, or `layout/`:

```powershell
python compile.py
```

`compile.py` generates all derived assets before invoking `latexmk` for the main PDF and every player packet. It prints the final PDF, generated-asset, and player-packet paths. Run `python tools/generate_player_packets.py` only when you need to refresh the derived assets without compiling the PDFs.

It uses only the Python standard library and writes derived files under `generated/`:

- relationship-map reference counts in CSV and JSON;
- an SVG graph, a Graphviz DOT source, and a TikZ companion that PDFLaTeX can embed; and
- an editable Mermaid (`.mmd`) mystery-resolution graph plus matching SVG and TikZ renderings; and
- one standalone, player-safe `player_packet.tex` file for each declared character.

The packets snapshot the current public rules and the character's own sheet. They do not distribute GM-only notes, the relationship map, clues, mysteries, the complete background, or other character sheets. Edit the sources in `content/` and `config/`; do not edit `generated/`.

The player-packet document is maintained in `layout/player_packet.template.tex`; `layout/player_packet_entity.template.tex` defines one entity-registration entry. Both use `@@UPPERCASE_TOKENS@@`, which the generator validates against the values it supplies.

Generated README and SVG layouts live in `tools/player_packets/templates/`. The renderer supplies their `@@UPPERCASE_TOKENS@@` values, keeping the generated document structures editable without changing Python.

Add `\shortdescription{...}` inside a `\CharacterSheet` to include that text in the generated character overview. Character images are read from `config/character_imgs/<character-id>.<extension>`; supported extensions are PNG, JPG, JPEG, and PDF. When no matching image exists, the overview uses `config/character_imgs/placeholder.png`.

The GM document checks for `generated/relationship_graph.svg`. When it is present, it renders the matching generated TikZ graph immediately after the relationship and GM notes; when it is absent, the document compiles without a graph.

Put venue photos in `content/assets/space/` (PNG, JPG, JPEG, or PDF). The build creates `generated/space_photos.tex` from those files, using `tools/player_packets/templates/space_photo.template.tex` for each photo and `space_photo_collection.template.tex` for the gallery-wide layout. `\ShowSpacePhotos` includes that file when it exists; otherwise it displays `No image in assets\space`.

Declare a mystery with a stable label, visible title, and body, then add ordering arrows using the labels:

```tex
\MysterySheet{how-newcomer-was-killed}{How newcomer was killed}{...}
\MysterySheet{who-killed-newcomer}{Who killed newcomer}{...}
\MysteryDependency{how-newcomer-was-killed}{who-killed-newcomer}
```

The generator writes `generated/mystery_order.mmd` for Mermaid-compatible editors and matching SVG/TikZ graphs. The GM document includes the TikZ graph in its Mysteries section only when the generated SVG exists.

Each generated TeX packet can be compiled from the repository root, for example:

```powershell
latexmk -pdf -outdir=target/players/usurper generated/players/usurper/player_packet.tex
```

The generator also reports source consistency issues in `generated/relationship_analysis.json`. In the current game, `newcomerlover` and `prevnewcomerlover` are configured in `config/characters.tex`, while their actual character IDs are `lover` and `prevlover`; that report makes such mismatches visible without preventing a build.
