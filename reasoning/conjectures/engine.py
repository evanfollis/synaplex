"""Conjecture-plane generator using subscription CLIs; output has zero authority."""
from __future__ import annotations
import datetime as dt
import json, os, sys
from pathlib import Path
from jsonschema import Draft202012Validator
from lab.runner.providers import default_pool
ROOT=Path(__file__).resolve().parents[2]
PROMPT=(ROOT/"reasoning/conjectures/conjecture-prompt.md").read_text()
RESULT_SCHEMA=json.loads((ROOT/"reasoning/conjectures/result.schema.json").read_text())
DEFAULT_TRACE=Path("/opt/workspace/runtime/conjectures/traces.jsonl")

def build_input(source_records):
    return PROMPT+"\n\nSourceObservation records (not Evidence):\n"+json.dumps(source_records,ensure_ascii=False,indent=2)

def _trace_path():
    return Path(os.environ.get("SYNAPLEX_CONJECTURE_TRACE_PATH", DEFAULT_TRACE))

def record_trace(record):
    """Durably append a replayable full-fidelity trace outside the public projection."""
    path=_trace_path(); path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    os.chmod(path.parent,0o700)
    flags=os.O_WRONLY|os.O_CREAT|os.O_APPEND
    fd=os.open(path,flags,0o600)
    try:
        payload=(json.dumps(record,ensure_ascii=False,separators=(",",":"))+"\n").encode()
        written=0
        while written<len(payload): written+=os.write(fd,payload[written:])
        os.fsync(fd)
    finally: os.close(fd)

def curate_conjecture(result):
    """Return a validated conjecture candidate; rejection is never publishable."""
    Draft202012Validator(RESULT_SCHEMA).validate(result)
    if result["kind"] != "conjecture":
        raise ValueError("rejection cannot enter the public conjecture registry")
    return dict(result)

def generate(source_records):
    prompt=build_input(source_records)
    completion=default_pool(role="conjecture-engine").complete(prompt,timeout_s=240)
    text=completion.text.strip(); start=text.find("{"); end=text.rfind("}")
    if start<0 or end<start: raise ValueError("model output did not contain a JSON object")
    result=json.loads(text[start:end+1])
    Draft202012Validator(RESULT_SCHEMA).validate(result)
    result["epistemic_status"]="conjectural" if result["kind"]=="conjecture" else "rejected"
    result["generation"]={"provider":completion.provider,"model":completion.model,"fallback_from":completion.fallback_from}
    record_trace({"captured_at":dt.datetime.now(dt.timezone.utc).isoformat(),"source_records":source_records,"prompt":prompt,"raw_output":completion.text,"output":result,"provider":completion.provider,"model":completion.model,"fallback_from":completion.fallback_from})
    return result

if __name__=="__main__": print(json.dumps(generate(json.load(sys.stdin)),indent=2,ensure_ascii=False))
