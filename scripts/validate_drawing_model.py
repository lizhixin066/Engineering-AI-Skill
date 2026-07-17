#!/usr/bin/env python3
"""Validate a structured drawing extraction model and write an issue report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.drawing import DrawingModelError, validate_drawing_model  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="校验工程图纸结构化识读模型")
    parser.add_argument("input", type=Path, help="图纸识读模型 JSON")
    parser.add_argument("--output", type=Path, required=True, help="问题报告 JSON")
    parser.add_argument("--strict", action="store_true", help="警告也视为不通过")
    args = parser.parse_args()
    try:
        with args.input.open(encoding="utf-8") as stream:
            report = validate_drawing_model(json.load(stream), strict=args.strict)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    except (OSError, json.JSONDecodeError, DrawingModelError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    if not report["passed"]:
        print(f"校验未通过：{report['summary']['errors']} 个错误，{report['summary']['warnings']} 个警告", file=sys.stderr)
        return 2
    print("图纸模型校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
