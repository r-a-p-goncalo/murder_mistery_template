# Language packs

The default authored game is English. Build it with:

```powershell
python compile.py --language en
```

Build a Portuguese (Portugal) version with:

```powershell
python compile.py --language pt-PT
```

Each locale mirrors the default file's path beneath `languages/<locale>/`.
For example, an overlay at `languages/pt-PT/content/general_rules.tex`
replaces `content/general_rules.tex`; an absent overlay falls back to the
default source. Use `\MMInput{...}` for authored project inputs so that TeX
and the Python packet generator use the same lookup rules.

`strings.tex` is required for every locale and contains short repeated labels.
Use full-file overlays for narrative prose, character sheets, clues, and game
configuration. A locale may also override layout or generator templates by
mirroring their paths, such as
`languages/pt-PT/layout/player_packet.template.tex`.

Keep semantic commands such as `\MMInput`, `\GMNotes`,
`\MMRelationshipMapHeading`, and `\MMHostGuidanceHeading` intact in an
overlay. They are language-neutral markers used by the main document and the
player-packet generator; translate their visible wording through `strings.tex`.

Derived files and PDFs are namespaced by language: `generated/<locale>/`,
`target/main/<locale>/`, and `target/players/<locale>/`.

While a translation is in progress, fallbacks are intentional. Before calling
it complete, run `python compile.py --language pt-PT --strict-language`.
That command checks every path in the pack's `manifest.txt`; update that list
when adding authored source files that need a full translation.
