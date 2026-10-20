import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from floorplan_qa import compare
ROOT=Path(__file__).resolve().parents[1]
src=json.loads((ROOT/"examples/synthetic_source.json").read_text())
dst=json.loads((ROOT/"examples/synthetic_reconstruction.json").read_text())

class OriginalSyntheticQA(unittest.TestCase):
    def test_example_contains_expected_independent_findings(self):
        report=compare(src,dst)
        self.assertEqual(report["summary"],{"fail":4,"review":1,"pass":False})
        self.assertEqual({f["code"] for f in report["findings"]},
            {"FIXTURE_CLASSIFIED_AS_WALL","WALL_ENDPOINT_DRIFT","MISSING_OPENING",
             "OPENING_DIMENSION_DRIFT","UNCERTAIN_SOURCE_DIMENSION"})
    def test_identical_drawing_model_is_clean(self):
        r=compare(src,src)
        self.assertEqual(r["findings"],[])
        self.assertTrue(r["summary"]["pass"])
    def test_wall_direction_reverse_is_equivalent(self):
        s=copy.deepcopy(src);m=copy.deepcopy(src)
        w=m["walls"][0]
        w["x1"],w["x2"]=w["x2"],w["x1"]
        w["y1"],w["y2"]=w["y2"],w["y1"]
        self.assertTrue(compare(s,m)["summary"]["pass"])
    def test_small_numeric_noise_under_tolerance_passes(self):
        m=copy.deepcopy(src);m["walls"][0]["x1"]+=0.04
        self.assertTrue(compare(src,m)["summary"]["pass"])
    def test_wall_delta_over_tolerance_is_fail(self):
        m=copy.deepcopy(src);m["walls"][0]["y2"]+=0.2
        self.assertEqual(compare(src,m)["findings"][0]["code"],"WALL_ENDPOINT_DRIFT")
    def test_uncertain_source_not_spurious_fail(self):
        m=copy.deepcopy(src);m["rooms"][0]["width_m"]+=0.2
        rep=compare(src,m)
        self.assertEqual(rep["summary"]["fail"],0)
        self.assertEqual(rep["summary"]["review"],1)
    def test_precise_source_dimension_is_fail(self):
        m=copy.deepcopy(src);m["rooms"][1]["depth_m"]+=0.2
        self.assertEqual(compare(src,m)["summary"]["fail"],1)
    def test_missing_opening_is_fail(self):
        m=copy.deepcopy(src);m["openings"].pop()
        self.assertEqual(compare(src,m)["findings"][0]["code"],"MISSING_OPENING")
    def test_added_fixture_as_wall_is_fail(self):
        m=copy.deepcopy(src)
        m["walls"].append({"id":"cabinet-01","x1":0,"y1":0,"x2":1,"y2":0})
        self.assertEqual(compare(src,m)["findings"][0]["code"],"FIXTURE_CLASSIFIED_AS_WALL")
    def test_unknown_unmapped_wall_is_review_not_false_failure(self):
        m=copy.deepcopy(src)
        m["walls"].append({"id":"not-in-source","x1":0,"y1":0,"x2":1,"y2":0})
        self.assertEqual(compare(src,m)["summary"]["review"],1)
        self.assertEqual(compare(src,m)["summary"]["fail"],0)
    def test_duplicate_identity_rejected(self):
        m=copy.deepcopy(src);m["openings"].append(copy.deepcopy(m["openings"][0]))
        with self.assertRaises(ValueError):compare(src,m)
    def test_nonfinite_and_boolean_numbers_rejected(self):
        for val in (float('nan'),float('inf'),True):
            m=copy.deepcopy(src);m["walls"][0]["x1"]=val
            with self.assertRaises(ValueError):compare(src,m)
    def test_negative_or_zero_width_rejected(self):
        for val in (-1,0):
            m=copy.deepcopy(src);m["rooms"][0]["width_m"]=val
            with self.assertRaises(ValueError):compare(src,m)
    def test_invalid_tolerances_fail(self):
        for val in (0,-1,1.1,True):
            with self.assertRaises(ValueError):compare(src,src,val)
    def test_inputs_are_never_mutated(self):
        a,b=copy.deepcopy(src),copy.deepcopy(dst)
        compare(src,dst)
        self.assertEqual(src,a)
        self.assertEqual(dst,b)
    def test_json_report_serializes(self):
        self.assertIn("SYNTHETIC_OFFLINE_EXAMPLE",json.dumps(compare(src,dst)))
if __name__=="__main__":unittest.main()
