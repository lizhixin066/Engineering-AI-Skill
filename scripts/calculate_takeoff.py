#!/usr/bin/env python3
"""Generate a JSON calculation book and optional Excel-compatible CSV summary."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.quantity import QuantityError, calculate_document  # noqa: E402


def write_csv(path: Path, results: list[dict]) -> None:
    fields = ["id", "description", "type", "unit", "gross_quantity", "net_quantity", "quantity", "formula", "source_refs", "status", "warnings"]
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in results:
            row = item.copy()
            row["source_refs"] = " | ".join(row["source_refs"])
            row["warnings"] = " | ".join(row["warnings"])
            writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser(description="生成可追溯工程量计算书")
    parser.add_argument("input", type=Path, help="已审核的工程量 JSON")
    parser.add_argument("--output", type=Path, required=True, help="计算书 JSON 输出路径")
    parser.add_argument("--csv", type=Path, help="可导入 Excel 的汇总 CSV 路径")
    parser.add_argument("--strict", action="store_true", help="拒绝无来源或非 confirmed 项")
    args = parser.parse_args()
    try:
        with args.input.open(encoding="utf-8") as stream:
            result = calculate_document(json.load(stream), strict=args.strict)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.csv:
            args.csv.parent.mkdir(parents=True, exist_ok=True)
            write_csv(args.csv, result["results"])
    except (OSError, json.JSONDecodeError, QuantityError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
