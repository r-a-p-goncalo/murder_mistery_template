#!/usr/bin/env python3
"""Generate player-safe LaTeX packets and relationship-map analysis.

This compatibility entry point delegates to the focused modules in
``tools/player_packets/``. Run ``python compile.py`` for the complete build.
"""

if __package__:
    from .player_packets.generator import main
else:
    from player_packets.generator import main


if __name__ == "__main__":
    raise SystemExit(main())
