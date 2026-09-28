# Dynamic player packets

Run the generator from the repository root after changing `content/` or `config/`:

```powershell
python tools/generate_player_packets.py
```

It uses only the Python standard library and writes derived files under `generated/`:

- relationship-map reference counts in CSV and JSON;
- an SVG graph, a Graphviz DOT source, and a TikZ companion that PDFLaTeX can embed; and
- one standalone, player-safe `player_packet.tex` file for each declared character.

The packets snapshot the current public rules and the character's own sheet. They do not distribute GM-only notes, the relationship map, clues, mysteries, the complete background, or other character sheets. Edit the sources in `content/` and `config/`; do not edit `generated/`.

The GM document checks for `generated/relationship_graph.svg`. When it is present, it renders the matching generated TikZ graph immediately after the relationship and GM notes; when it is absent, the document compiles without a graph.

Each generated TeX packet can be compiled from the repository root, for example:

```powershell
latexmk -pdf -outdir=target/players/usurper generated/players/usurper/player_packet.tex
```

The generator also reports source consistency issues in `generated/relationship_analysis.json`. In the current game, `newcomerlover` and `prevnewcomerlover` are configured in `config/characters.tex`, while their actual character IDs are `lover` and `prevlover`; that report makes such mismatches visible without preventing a build.
