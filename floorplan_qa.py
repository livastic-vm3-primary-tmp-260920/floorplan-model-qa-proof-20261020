#!/usr/bin/env python3
"""Original offline synthetic source-drawing versus reconstructed-model QA.

Deterministic evidence, not architectural certification. No network, auth,
customer address, CAD import, account creation, or real-world accuracy claim.
"""
from __future__ import annotations
import argparse
import json
from math import hypot, isfinite
from pathlib import Path


def _id(item):
    v = item.get("id")
    if not isinstance(v, str) or not v.strip() or len(v) > 100:
        raise ValueError("each object needs a non-empty unique string id")
    return v


def _num(item, key, minimum=None):
    v = item.get(key)
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v):
        raise ValueError(f"{key} must be a finite numeric value")
    if minimum is not None and v < minimum:
        raise ValueError(f"{key} below allowed minimum")
    return float(v)


def _index(items, field):
    if not isinstance(items, list):
        raise ValueError(f"{field} must be an array")
    result = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError(f"bad {field} object")
        ident = _id(item)
        if ident in result:
            raise ValueError(f"duplicate id in {field}: {ident}")
        result[ident] = item
    return result


def _validate(doc):
    if not isinstance(doc, dict) or doc.get("unit") != "m":
        raise ValueError("source and reconstruction must state unit: m")
    maps = {k: _index(doc.get(k, []), k) for k in ("walls", "rooms", "openings", "fixtures")}
    for ob in maps["walls"].values():
        for k in ("x1", "y1", "x2", "y2"):
            _num(ob, k)
    for ob in maps["rooms"].values():
        _num(ob, "width_m", 0.000001)
        _num(ob, "depth_m", 0.000001)
        if "source_uncertain" in ob and not isinstance(ob["source_uncertain"], bool):
            raise ValueError("source_uncertain must be boolean")
    for ob in maps["openings"].values():
        _num(ob, "offset_m", 0)
        _num(ob, "width_m", 0.000001)
        if not isinstance(ob.get("wall_id"), str):
            raise ValueError("opening wall_id must be a string")
    return maps


def _dist(x, y, u, v):
    return hypot(x-u, y-v)


def _wall_delta(a, b):
    p = (_num(a, "x1"), _num(a, "y1"))
    q = (_num(a, "x2"), _num(a, "y2"))
    r = (_num(b, "x1"), _num(b, "y1"))
    s = (_num(b, "x2"), _num(b, "y2"))
    forward = max(_dist(*p, *r), _dist(*q, *s))
    reverse = max(_dist(*p, *s), _dist(*q, *r))
    return min(forward, reverse)


def compare(source, reconstruction, tolerance_m=0.10):
    if isinstance(tolerance_m, bool) or not isinstance(tolerance_m, (float, int)) or not isfinite(tolerance_m) or not 0 < tolerance_m <= 1:
        raise ValueError("tolerance_m requires 0 < tolerance <= 1m")
    a, b = _validate(source), _validate(reconstruction)
    findings = []

    def issue(code, severity, kind, ident, detail, observed=None, expected=None):
        findings.append({"code": code, "severity": severity, "kind": kind, "id": ident,
                         "detail": detail, "observed": observed, "expected": expected})
    for kind in ("walls", "rooms", "openings"):
        missing = sorted(set(a[kind]) - set(b[kind]))
        for ident in missing:
            issue("MISSING_"+kind[:-1].upper(), "fail", kind, ident,
                  "Source element absent in reconstructed model")
        extras = sorted(set(b[kind])-set(a[kind]))
        for ident in extras:
            special = kind == "walls" and ident in a["fixtures"]
            issue("FIXTURE_CLASSIFIED_AS_WALL" if special else "UNREFERENCED_"+kind[:-1].upper(),
                  "fail" if special else "review", kind, ident,
                  "Source fixture incorrectly modeled as structural wall" if special
                  else "Element not found in source; requires provenance check")

    for ident in sorted(set(a["walls"]) & set(b["walls"])):
        delta = _wall_delta(a["walls"][ident],b["walls"][ident])
        if delta > tolerance_m:
            issue("WALL_ENDPOINT_DRIFT", "fail", "walls", ident,
                  "Maximum matched endpoint shift exceeds stated tolerance",
                  observed=round(delta,4), expected=f"<= {tolerance_m}m")
    for ident in sorted(set(a["rooms"]) & set(b["rooms"])):
        src, mod = a["rooms"][ident], b["rooms"][ident]
        for dim in ("width_m","depth_m"):
            delta = abs(src[dim]-mod[dim])
            if delta > tolerance_m:
                uncertain = src.get("source_uncertain", False)
                issue("UNCERTAIN_SOURCE_DIMENSION" if uncertain else "ROOM_DIMENSION_DRIFT",
                      "review" if uncertain else "fail", "rooms", ident,
                      f"{dim} differs; source confidence gates severity",
                      observed=mod[dim],expected=src[dim])
    for ident in sorted(set(a["openings"]) & set(b["openings"])):
        src, mod = a["openings"][ident], b["openings"][ident]
        if src["wall_id"] != mod["wall_id"]:
            issue("OPENING_ON_DIFFERENT_WALL","fail","openings",ident,
                  "Opening attached to a different wall",
                  observed=mod["wall_id"], expected=src["wall_id"])
        for field in ("offset_m","width_m"):
            if abs(src[field]-mod[field])>tolerance_m:
                issue("OPENING_DIMENSION_DRIFT","fail","openings",ident,
                      field+" differs beyond tolerance",
                      observed=mod[field],expected=src[field])
    findings.sort(key=lambda x:(x["kind"],x["id"],x["code"],x["detail"]))
    return {
        "report_type": "SYNTHETIC_OFFLINE_EXAMPLE_NOT_CUSTOMER_DELIVERY",
        "unit": "m", "tolerance_m": tolerance_m,
        "summary":{"fail":sum(x["severity"]=="fail" for x in findings),
                   "review":sum(x["severity"]=="review" for x in findings),
                   "pass":len(findings)==0},
        "findings": findings,
        "limitations":[
            "Illustrative synthetic structured data, not a real customer plan or verified reconstruction.",
            "No CAD/PDF/image recognition, building-code validation, occupancy or safety certification.",
            "Conflicting uncertain source dimensions are REVIEW, not falsely asserted defects.",
            "Every finding needs source provenance and human inspection before use in production."
        ]
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--model",type=Path,required=True)
    parser.add_argument("--tolerance-m",type=float,default=0.10)
    ns=parser.parse_args()
    s=json.loads(ns.source.read_text(encoding="utf-8"))
    m=json.loads(ns.model.read_text(encoding="utf-8"))
    print(json.dumps(compare(s,m,ns.tolerance_m),indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
