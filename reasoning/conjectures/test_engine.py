import json, os, tempfile, unittest
from pathlib import Path
from jsonschema import Draft202012Validator
from reasoning.conjectures.engine import RESULT_SCHEMA, build_input, curate_conjecture, record_trace
ROOT=Path(__file__).resolve().parents[2]
class EngineTests(unittest.TestCase):
    def test_prompt_preserves_epistemic_boundary(self):
        prompt=build_input([{"id":"src:x","title":"x"}]); self.assertIn("never findings or Evidence",prompt); self.assertIn("preregistered Claim",prompt); self.assertIn("never inspect files or invoke tools",prompt)
    def test_result_union_separates_rejection_from_conjecture(self):
        Draft202012Validator(RESULT_SCHEMA).validate({"kind":"rejection","source_ids":["src:a"],"failure_modes":["same domain"],"rationale":"No cross-domain mechanism.","remediation":"Provide a second typed source from another domain."})
        with self.assertRaises(Exception):
            Draft202012Validator(RESULT_SCHEMA).validate({"kind":"rejection","title":"laundered conjecture","source_ids":[],"failure_modes":["x"],"rationale":"x","remediation":"x"})
    def test_rejection_cannot_enter_public_curation(self):
        rejection={"kind":"rejection","source_ids":["src:a"],"failure_modes":["missing type"],"rationale":"Not a transfer.","remediation":"Supply typed sources."}
        with self.assertRaisesRegex(ValueError,"cannot enter"):
            curate_conjecture(rejection)
    def test_curated_conjectures_are_complete_and_cross_domain(self):
        data=json.loads((ROOT/"reasoning/conjectures/conjectures.json").read_text()); sources={s["id"]:s for s in json.loads((ROOT/"sources/registry.json").read_text())["sources"]}
        required={"analogy_map","disanalogies","competing_explanations","falsifiers","preconditions"}
        for item in data["conjectures"]:
            self.assertTrue(required <= set(item)); self.assertGreaterEqual(len({sources[x]["domain"] for x in item["source_ids"]}),2); self.assertLessEqual(item["redundancy_score"],1)
    def test_trace_is_lossless_append_only_and_private(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"private"/"traces.jsonl"; previous=os.environ.get("SYNAPLEX_CONJECTURE_TRACE_PATH")
            os.environ["SYNAPLEX_CONJECTURE_TRACE_PATH"]=str(path)
            try:
                record={"prompt":"full input","raw_output":"full output","output":{"title":"x"}}
                record_trace(record); record_trace(record)
                self.assertEqual([json.loads(line) for line in path.read_text().splitlines()],[record,record])
                self.assertEqual(path.stat().st_mode & 0o777,0o600)
                self.assertEqual(path.parent.stat().st_mode & 0o777,0o700)
            finally:
                if previous is None: os.environ.pop("SYNAPLEX_CONJECTURE_TRACE_PATH",None)
                else: os.environ["SYNAPLEX_CONJECTURE_TRACE_PATH"]=previous
if __name__=="__main__": unittest.main()
