"""Validate and measure the curated SourceObservation registry."""
from __future__ import annotations
import json, math
from collections import Counter
from pathlib import Path
from jsonschema import Draft202012Validator
from intake.hashing import canonicalize_url

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "sources/registry.json"
SCHEMA = ROOT / "sources/registry.schema.json"

def load_registry():
    data=json.loads(REGISTRY.read_text()); schema=json.loads(SCHEMA.read_text())
    Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).validate(data)
    ids=[s["id"] for s in data["sources"]]; urls=[canonicalize_url(s["url"]) for s in data["sources"]]
    if len(ids)!=len(set(ids)) or len(urls)!=len(set(urls)): raise ValueError("source identity or canonical URL collision")
    return data

def metrics(data=None):
    data=data or load_registry(); sources=data["sources"]; counts=Counter(s["domain"] for s in sources); n=len(sources)
    entropy=-sum((v/n)*math.log(v/n,2) for v in counts.values())
    max_entropy=math.log(len(counts),2) if counts else 1
    return {"source_count":n,"domain_count":len(counts),"domain_balance":round(entropy/max_entropy,3),"redundant_url_count":n-len({canonicalize_url(s["url"]) for s in sources}),"mean_quality":round(sum(s["quality"] for s in sources)/n,3),"retrieved_at_max":max(s["retrieved_at"] for s in sources)}

if __name__ == "__main__": print(json.dumps(metrics(),indent=2))
