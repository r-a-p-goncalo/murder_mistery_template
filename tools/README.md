# Dynamic player packets

Run the complete English build from the repository root after changing `content/`, `config/`, `layout/`, or a language pack:

```powershell
python compile.py
```

Use `--language` to select a locale. Portuguese (Portugal) currently has a
scaffolded pack with translated interface strings and fallback to the English
authored files until their overlays are added:

```powershell
python compile.py --language pt-PT
```

To compile and also collect every player PDF in `target/organized_characters/`
under the configured person's name, run:

```powershell
python compile_and_organize.py
```

The organizer creates both `<person>_with_rules.pdf` and
`<person>_without_rules.pdf`. Person names are converted to portable lowercase
snake case, so `Inês T.` becomes `ines_t_with_rules.pdf`. The character ID is
used only to locate the compiler output and never appears in the organized
filename.

The build keeps derived files separate per locale: `generated/<locale>/`,
`target/main/<locale>/`, and `target/players/<locale>/`. See
[`languages/README.md`](../languages/README.md) for the overlay convention and
the `--strict-language` completeness check.

`compile.py` generates all derived assets before invoking `latexmk` for the main PDF and both variants of every player packet. It prints the final PDF, generated-asset, and player-packet paths. Run `python tools/generate_player_packets.py --language pt-PT` only when you need to refresh one locale's derived assets without compiling the PDFs.

It uses only the Python standard library and writes derived files under `generated/<locale>/`:

- relationship-map reference counts in CSV and JSON;
- an SVG graph, a Graphviz DOT source, and a TikZ companion that PDFLaTeX can embed; and
- an editable Mermaid (`.mmd`) mystery-resolution graph plus matching SVG and TikZ renderings; and
- two standalone, player-safe files for each declared character: `player_packet_with_rules.tex` and `player_packet_without_rules.tex`.

The with-rules packet includes the public rules, the character overview, and the character's own sheet. The without-rules packet contains only its cover and the character's own sheet. The character's public short description remains in the overview of the with-rules packet but is removed from the detailed copy of their own sheet. Both variants omit GM-only notes, the relationship map, clues, mysteries, the complete background, and other character sheets. Edit the sources in `content/`, `config/`, and `languages/<locale>/`; do not edit `generated/`.

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
latexmk -pdf -outdir=target/players/en/example-character generated/en/players/example-character/player_packet_with_rules.tex
```

The generator also reports source consistency issues in `generated/relationship_analysis.json`. In the current game, `newcomerlover` and `prevnewcomerlover` are configured in `config/characters.tex`, while their actual character IDs are `lover` and `prevlover`; that report makes such mismatches visible without preventing a build.
