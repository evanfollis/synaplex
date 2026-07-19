import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent

class PublicCopyBoundaryTests(unittest.TestCase):
    def test_every_adjacent_track_names_its_non_evidence_boundary(self):
        expected={
            "src/pages/sources/index.astro":("cannot become Synaplex Evidence",),
            "src/pages/conjectures/index.astro":("upstream of Claims","Scores rank attention only"),
            "src/pages/case-studies/index.astro":("not Claims, Evidence, Decisions, or scientific findings",),
            "src/pages/research/index.astro":("Before registration",),
        }
        for rel, phrases in expected.items():
            text=(ROOT/rel).read_text()
            for phrase in phrases:
                self.assertIn(phrase,text,rel)

    def test_zero_findings_copy_is_explicit(self):
        text=(ROOT/"src/pages/index.astro").read_text()
        self.assertIn("No claim has yet completed the full Evidence-to-Decision standard",text)

if __name__ == "__main__": unittest.main()
