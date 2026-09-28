import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "generate_player_packets.py"
SPEC = importlib.util.spec_from_file_location("generate_player_packets", MODULE_PATH)
assert SPEC and SPEC.loader
GENERATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GENERATOR
SPEC.loader.exec_module(GENERATOR)


class GeneratePlayerPacketsTest(unittest.TestCase):
    def test_generates_self_contained_packets_and_relationship_outputs(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "generated"
            analysis = GENERATOR.build(ROOT, output)

            self.assertEqual(len(analysis["character_reference_counts"]), 10)
            self.assertGreater(len(analysis["relationship_map_entries"]), 0)
            self.assertTrue((output / "relationship_counts.csv").is_file())
            self.assertTrue((output / "relationship_graph.svg").is_file())
            self.assertTrue((output / "relationship_graph.dot").is_file())
            graph_tex = (output / "relationship_graph.tex").read_text(encoding="utf-8")
            self.assertIn("\\begin{tikzpicture}", graph_tex)
            self.assertIn("opacity=1.00", graph_tex)

            packet = (output / "players" / "usurper" / "player_packet.tex").read_text(encoding="utf-8")
            self.assertIn("\\begin{document}", packet)
            self.assertIn("\\section{General rules}", packet)
            self.assertIn("\\CharacterSheet{usurper}", packet)
            self.assertNotIn("\\subsection{How to create a game}", packet)
            self.assertNotIn("\\input{content/complete-background", packet)

            validation = analysis["validation"]
            self.assertIn("newcomerlover", validation["configured_character_ids_without_sheets"])
            self.assertIn("lover", validation["characters_without_configured_player_name"])

            # A changed report created by an earlier run remains safe to replace.
            report = output / "relationship_analysis.json"
            report.write_text(json.dumps({"generated_by": "tools/generate_player_packets.py", "stale": True}), encoding="utf-8")
            regenerated = GENERATOR.build(ROOT, output)
            self.assertEqual(len(regenerated["character_reference_counts"]), 10)


if __name__ == "__main__":
    unittest.main()
