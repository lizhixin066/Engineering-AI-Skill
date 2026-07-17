import copy
import unittest

from engine.drawing import validate_drawing_model


def length(value, unit="m"):
    return {"value": value, "unit": unit}


def valid_model():
    return {
        "project": "测试工程",
        "drawings": [{
            "drawing_no": "A-101", "title": "一层平面图", "discipline": "architecture",
            "revision": "R01", "scale": "1:100", "unit": "mm", "status": "active",
        }],
        "axis_chains": [{
            "id": "X", "direction": "x", "total": length(6),
            "segments": [
                {"from": "1", "to": "2", "distance": length(3)},
                {"from": "2", "to": "3", "distance": length(3)},
            ],
        }],
        "elevations": [{
            "id": "室外地坪", "value": length(-0.45), "source_refs": ["A-101/标高"],
            "status": "confirmed", "confidence": "high",
        }],
        "components": [{
            "id": "W-01", "category": "wall", "level": "1F", "source_refs": ["A-101/轴1-3/A"],
            "status": "confirmed", "confidence": "high",
            "measurements": {"length": length(6), "height": length(3), "thickness": length(200, "mm")},
        }],
        "ocr_checks": [{
            "id": "ocr-1", "first_read": "W-01 200", "second_read": "W-01 200", "source_ref": "A-101/墙标注",
        }],
    }


class DrawingModelTests(unittest.TestCase):
    def test_valid_model_passes_strict_validation(self):
        report = validate_drawing_model(valid_model(), strict=True)
        self.assertTrue(report["passed"])
        self.assertEqual(report["summary"]["errors"], 0)
        self.assertEqual(report["summary"]["warnings"], 0)

    def test_axis_chain_mismatch_is_blocking(self):
        model = valid_model()
        model["axis_chains"][0]["total"] = length(6.1)
        report = validate_drawing_model(model)
        self.assertFalse(report["passed"])
        self.assertIn("AXIS_CHAIN_MISMATCH", {issue["code"] for issue in report["issues"]})

    def test_negative_elevation_is_allowed(self):
        report = validate_drawing_model(valid_model())
        self.assertNotIn("ELEVATION_VALUE_INVALID", {issue["code"] for issue in report["issues"]})

    def test_low_confidence_cannot_be_confirmed(self):
        model = valid_model()
        model["components"][0]["confidence"] = "low"
        report = validate_drawing_model(model)
        self.assertIn("LOW_CONFIDENCE_CONFIRMED", {issue["code"] for issue in report["issues"]})

    def test_ocr_disagreement_is_blocking(self):
        model = valid_model()
        model["ocr_checks"][0]["second_read"] = "W-01 300"
        report = validate_drawing_model(model)
        self.assertIn("OCR_MISMATCH", {issue["code"] for issue in report["issues"]})

    def test_warning_only_fails_in_strict_mode(self):
        model = valid_model()
        del model["components"][0]["measurements"]["thickness"]
        normal = validate_drawing_model(copy.deepcopy(model), strict=False)
        strict = validate_drawing_model(copy.deepcopy(model), strict=True)
        self.assertTrue(normal["passed"])
        self.assertFalse(strict["passed"])
        self.assertEqual(normal["summary"]["warnings"], 1)

    def test_multiple_active_revisions_are_rejected(self):
        model = valid_model()
        second = copy.deepcopy(model["drawings"][0])
        second["revision"] = "R02"
        model["drawings"].append(second)
        report = validate_drawing_model(model)
        self.assertIn("MULTIPLE_ACTIVE_REVISIONS", {issue["code"] for issue in report["issues"]})

    def test_invalid_top_level_collection_is_reported(self):
        model = valid_model()
        model["components"] = "not-a-list"
        report = validate_drawing_model(model)
        self.assertIn("COLLECTION_INVALID", {issue["code"] for issue in report["issues"]})

    def test_non_finite_measurement_is_rejected(self):
        model = valid_model()
        model["components"][0]["measurements"]["length"] = length("NaN")
        report = validate_drawing_model(model)
        self.assertIn("MEASUREMENT_INVALID", {issue["code"] for issue in report["issues"]})


if __name__ == "__main__":
    unittest.main()
