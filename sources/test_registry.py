import json, unittest
from sources.registry import load_registry, metrics
class RegistryTests(unittest.TestCase):
    def test_registry_is_valid_diverse_and_deduplicated(self):
        data=load_registry(); m=metrics(data)
        self.assertEqual(m["domain_count"],7); self.assertEqual(m["redundant_url_count"],0); self.assertGreaterEqual(m["domain_balance"],0.85)
    def test_identity_is_digest_derived(self):
        for source in load_registry()["sources"]: self.assertEqual(source["id"],"src:"+source["content_digest"][7:23])
    def test_sources_are_observations_not_evidence(self):
        raw=json.dumps(load_registry()); self.assertNotIn('"Evidence"',raw); self.assertNotIn('"Decision"',raw)
if __name__ == "__main__": unittest.main()
