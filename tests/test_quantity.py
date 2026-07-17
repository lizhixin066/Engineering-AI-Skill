import unittest

from engine.quantity import QuantityError, calculate_document


def length(value, unit="m"):
    return {"value": value, "unit": unit}


class QuantityCalculationTests(unittest.TestCase):
    def test_slab_converts_mm_and_deducts_opening(self):
        result = calculate_document({"items": [{
            "id": "slab-1", "type": "slab", "source_refs": ["S-101"], "status": "confirmed",
            "inputs": {"length": length(6000, "mm"), "width": length(4000, "mm"), "thickness": length(120, "mm")},
            "options": {"deductions": [{"length": length(1000, "mm"), "width": length(1000, "mm"), "thickness": length(120, "mm")}]} } ]})
        self.assertEqual(result["results"][0]["net_quantity"], 2.76)

    def test_rebar_uses_diameter_theoretical_weight(self):
        result = calculate_document({"items": [{
            "id": "rb-1", "type": "rebar", "source_refs": ["S-201"], "status": "confirmed",
            "inputs": {"count": length(10, "each"), "length": length(6), "diameter": length(12, "mm")} } ]})
        self.assertEqual(result["results"][0]["quantity"], 53.333)

    def test_strict_mode_rejects_unconfirmed_item(self):
        with self.assertRaises(QuantityError):
            calculate_document({"items": [{
                "id": "pipe-1", "type": "pipe", "source_refs": ["P-101"], "status": "inferred",
                "inputs": {"length": length(2)} } ]}, strict=True)

    def test_rejects_over_deduction(self):
        with self.assertRaises(QuantityError):
            calculate_document({"items": [{
                "id": "area-1", "type": "area", "source_refs": ["A-101"], "status": "confirmed",
                "inputs": {"length": length(1), "width": length(1)},
                "options": {"deductions": [{"length": length(2), "width": length(1)}]} } ]})

    def test_rejects_non_finite_values(self):
        with self.assertRaises(QuantityError):
            calculate_document({"items": [{
                "id": "area-nan", "type": "area", "source_refs": ["A-101"], "status": "confirmed",
                "inputs": {"length": length("NaN"), "width": length(1)} } ]})


if __name__ == "__main__":
    unittest.main()
