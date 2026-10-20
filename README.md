# Source-to-Model QA — original synthetic example

This is independently authored **AI-assisted QA engineering source** supporting a truthful studio-vendor inquiry. It is **NOT a client contract, paid job, architectural credential, production building model, or proof of past client work**. No external/customer data is processed.

This demonstration compares two invented machine-readable interpretations of a floorplan, then emits deterministic discrepancy records.

## Genuine operations shown

- Reversed wall endpoints are geometrically equivalent.
- More than 0.10 m wall endpoint drift is reported.
- Source openings missing from the model and displaced openings are reported.
- Source fixtures mistakenly treated as load-bearing walls are flagged.
- Exact room measurements are compared, but **uncertain source lengths yield REVIEW, not fabricated FAIL**.
- Duplicate geometry IDs, malformed units, invalid numeric data and impossible dimensions fail closed.
- Sorted stable JSON report is suitable for follow-on human inspection.

## Reproduce

Requires Python 3.10+ standard library only; no network or private source files.

```bash
python3 -m unittest discover -s tests -v
python3 floorplan_qa.py --source examples/synthetic_source.json --model examples/synthetic_reconstruction.json
```

See `examples/synthetic_report.json` for recorded output. All assets original and invented; **no CAD importer, PDF/image recognition or 3D editor integration** is claimed. A genuine paid pilot needs a buyer's written brief, lawful data terms, permitted testing surface, acceptance criteria, turnaround and payment route agreed before work.
