"""Validation engine for traceable architectural and structural drawing models."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any


class DrawingModelError(ValueError):
    """Raised when the drawing-model document itself cannot be processed."""


DISCIPLINE_ALIASES = {
    "architecture": "architecture", "建筑": "architecture",
    "structure": "structure", "结构": "structure",
    "plumbing": "plumbing", "给排水": "plumbing",
    "hvac": "hvac", "暖通": "hvac",
    "electrical": "electrical", "电气": "electrical",
    "fire": "fire", "消防": "fire",
    "steel": "steel", "钢结构": "steel",
    "decoration": "decoration", "装修": "decoration",
    "landscape": "landscape", "园林": "landscape",
    "municipal": "municipal", "市政": "municipal",
    "road": "road", "道路": "road",
    "bridge": "bridge", "桥梁": "bridge",
}
DRAWING_STATUSES = {"active", "replaced", "pending"}
ITEM_STATUSES = {"confirmed", "inferred", "pending"}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
LENGTH_FACTORS = {"m": Decimal("1"), "mm": Decimal("0.001"), "cm": Decimal("0.01")}
AREA_FACTORS = {"m2": Decimal("1"), "mm2": Decimal("0.000001")}
COUNT_UNITS = {"each", "count", "个"}
SCALE_PATTERN = re.compile(r"^1\s*:\s*[1-9]\d*$")

CATEGORY_REQUIREMENTS: dict[str, dict[str, str]] = {
    "room": {"area": "area"},
    "wall": {"length": "length", "height": "length", "thickness": "length"},
    "door": {"width": "length", "height": "length", "count": "count"},
    "window": {"width": "length", "height": "length", "count": "count"},
    "column": {"section_width": "length", "section_depth": "length", "storey_height": "length", "count": "count"},
    "beam": {"length": "length", "width": "length", "height": "length", "count": "count"},
    "slab": {"area": "area", "thickness": "length"},
    "stair": {"width": "length", "storey_height": "length", "count": "count"},
    "foundation": {"length": "length", "width": "length", "height": "length", "count": "count"},
    "rebar": {"diameter": "length", "length": "length", "count": "count"},
    "opening": {"width": "length", "height": "length", "count": "count"},
    "pipe": {"length": "length"},
    "duct": {"length": "length"},
    "cable": {"length": "length"},
    "equipment": {"count": "count"},
}


def _decimal(value: Any, label: str, *, allow_negative: bool = False) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise DrawingModelError(f"{label} 必须为数字") from exc
    if not number.is_finite():
        raise DrawingModelError(f"{label} 必须为有限数值")
    if not allow_negative and number < 0:
        raise DrawingModelError(f"{label} 不得为负数")
    return number


def _measure(raw: Any, kind: str, label: str, *, allow_negative: bool = False) -> Decimal:
    if not isinstance(raw, dict) or "value" not in raw or "unit" not in raw:
        raise DrawingModelError(f"{label} 必须包含 value 和 unit")
    unit = str(raw["unit"]).strip().lower()
    if kind == "length":
        factors = LENGTH_FACTORS
    elif kind == "area":
        factors = AREA_FACTORS
    elif kind == "count":
        factors = {value: Decimal("1") for value in COUNT_UNITS}
    else:
        raise DrawingModelError(f"未知量纲 {kind!r}")
    if unit not in factors:
        raise DrawingModelError(f"{label} 的单位 {unit!r} 不适用于 {kind}")
    return _decimal(raw["value"], label, allow_negative=allow_negative) * factors[unit]


def _issue(issues: list[dict[str, str]], severity: str, code: str, message: str, entity: str) -> None:
    issues.append({"severity": severity, "code": code, "message": message, "entity": entity})


def _validate_status_and_confidence(
    item: dict[str, Any], issues: list[dict[str, str]], entity: str
) -> None:
    status = str(item.get("status", "pending")).lower()
    confidence = str(item.get("confidence", "low")).lower()
    if status not in ITEM_STATUSES:
        _issue(issues, "error", "ITEM_STATUS_INVALID", f"状态 {status!r} 无效", entity)
    if confidence not in CONFIDENCE_LEVELS:
        _issue(issues, "error", "CONFIDENCE_INVALID", f"置信度 {confidence!r} 无效", entity)
    if status == "confirmed" and confidence == "low":
        _issue(issues, "error", "LOW_CONFIDENCE_CONFIRMED", "低置信度内容不能标记为 confirmed", entity)
    if status == "inferred" and not str(item.get("inference_note", "")).strip():
        _issue(issues, "warning", "INFERENCE_NOTE_MISSING", "inferred 项缺少推断路径", entity)
    if status == "pending" and not str(item.get("pending_reason", "")).strip():
        _issue(issues, "warning", "PENDING_REASON_MISSING", "pending 项缺少待确认原因", entity)


def validate_drawing_model(data: dict[str, Any], strict: bool = False) -> dict[str, Any]:
    """Validate a drawing extraction model and return a stable issue report."""
    if not isinstance(data, dict):
        raise DrawingModelError("顶层必须是对象")
    issues: list[dict[str, str]] = []
    drawings = data.get("drawings")
    if not isinstance(drawings, list) or not drawings:
        raise DrawingModelError("顶层必须包含非空 drawings 数组")

    collections: dict[str, list[Any]] = {}
    for field in ("axis_chains", "elevations", "components", "ocr_checks"):
        value = data.get(field, [])
        if not isinstance(value, list):
            _issue(issues, "error", "COLLECTION_INVALID", f"顶层 {field} 必须是数组", f"document:{field}")
            value = []
        collections[field] = value

    drawing_numbers: set[str] = set()
    drawing_keys: set[tuple[str, str]] = set()
    active_numbers: set[str] = set()
    required_drawing_fields = ("drawing_no", "title", "discipline", "revision", "scale", "unit", "status")
    for index, drawing in enumerate(drawings, 1):
        entity = f"drawing:{index}"
        if not isinstance(drawing, dict):
            _issue(issues, "error", "DRAWING_NOT_OBJECT", "图纸记录必须是对象", entity)
            continue
        missing = [field for field in required_drawing_fields if not str(drawing.get(field, "")).strip()]
        if missing:
            _issue(issues, "error", "DRAWING_FIELDS_MISSING", "缺少字段：" + ", ".join(missing), entity)
        drawing_no = str(drawing.get("drawing_no", "")).strip()
        revision = str(drawing.get("revision", "")).strip()
        drawing_numbers.add(drawing_no)
        key = (drawing_no, revision)
        if drawing_no and revision and key in drawing_keys:
            _issue(issues, "error", "DRAWING_DUPLICATE", f"图号/版次重复：{drawing_no}/{revision}", entity)
        drawing_keys.add(key)
        discipline = str(drawing.get("discipline", "")).strip().lower()
        if discipline and discipline not in DISCIPLINE_ALIASES:
            _issue(issues, "error", "DISCIPLINE_UNSUPPORTED", f"不支持的专业：{discipline}", entity)
        scale = str(drawing.get("scale", "")).strip()
        if scale and not SCALE_PATTERN.fullmatch(scale):
            _issue(issues, "error", "SCALE_INVALID", f"比例格式无效：{scale}", entity)
        unit = str(drawing.get("unit", "")).strip().lower()
        if unit and unit not in LENGTH_FACTORS:
            _issue(issues, "error", "DRAWING_UNIT_INVALID", f"图纸单位无效：{unit}", entity)
        status = str(drawing.get("status", "")).strip().lower()
        if status and status not in DRAWING_STATUSES:
            _issue(issues, "error", "DRAWING_STATUS_INVALID", f"图纸状态无效：{status}", entity)
        if status == "active" and drawing_no:
            if drawing_no in active_numbers:
                _issue(issues, "error", "MULTIPLE_ACTIVE_REVISIONS", f"图号 {drawing_no} 有多个有效版本", entity)
            active_numbers.add(drawing_no)

    for index, chain in enumerate(collections["axis_chains"], 1):
        entity = f"axis_chain:{chain.get('id', index) if isinstance(chain, dict) else index}"
        if not isinstance(chain, dict):
            _issue(issues, "error", "AXIS_CHAIN_NOT_OBJECT", "轴网尺寸链必须是对象", entity)
            continue
        direction = str(chain.get("direction", "")).lower()
        if direction not in {"x", "y"}:
            _issue(issues, "error", "AXIS_DIRECTION_INVALID", "轴网方向必须是 x 或 y", entity)
        segments = chain.get("segments")
        if not isinstance(segments, list) or not segments:
            _issue(issues, "error", "AXIS_SEGMENTS_MISSING", "轴网尺寸链缺少 segments", entity)
            continue
        try:
            segment_total = sum(
                (_measure(segment.get("distance"), "length", f"{entity}.segments[{position}].distance")
                 for position, segment in enumerate(segments, 1)),
                Decimal("0"),
            )
            expected_total = _measure(chain.get("total"), "length", f"{entity}.total")
            if abs(segment_total - expected_total) > Decimal("0.001"):
                difference_mm = (segment_total - expected_total) * Decimal("1000")
                _issue(issues, "error", "AXIS_CHAIN_MISMATCH", f"分段合计与总尺寸相差 {difference_mm} mm", entity)
        except (DrawingModelError, AttributeError) as exc:
            _issue(issues, "error", "AXIS_MEASURE_INVALID", str(exc), entity)

    elevation_ids: set[str] = set()
    for index, elevation in enumerate(collections["elevations"], 1):
        entity = f"elevation:{elevation.get('id', index) if isinstance(elevation, dict) else index}"
        if not isinstance(elevation, dict):
            _issue(issues, "error", "ELEVATION_NOT_OBJECT", "标高记录必须是对象", entity)
            continue
        elevation_id = str(elevation.get("id", "")).strip()
        if not elevation_id:
            _issue(issues, "error", "ELEVATION_ID_MISSING", "标高缺少 id", entity)
        elif elevation_id in elevation_ids:
            _issue(issues, "error", "ELEVATION_DUPLICATE", f"标高 id 重复：{elevation_id}", entity)
        elevation_ids.add(elevation_id)
        try:
            _measure(elevation.get("value"), "length", f"{entity}.value", allow_negative=True)
        except DrawingModelError as exc:
            _issue(issues, "error", "ELEVATION_VALUE_INVALID", str(exc), entity)
        _validate_status_and_confidence(elevation, issues, entity)
        if not elevation.get("source_refs"):
            _issue(issues, "error", "SOURCE_MISSING", "标高缺少来源", entity)

    component_keys: set[tuple[str, str]] = set()
    for index, component in enumerate(collections["components"], 1):
        entity = f"component:{component.get('id', index) if isinstance(component, dict) else index}"
        if not isinstance(component, dict):
            _issue(issues, "error", "COMPONENT_NOT_OBJECT", "构件记录必须是对象", entity)
            continue
        component_id = str(component.get("id", "")).strip()
        level = str(component.get("level", "")).strip()
        category = str(component.get("category", "")).strip().lower()
        if not component_id or not level or not category:
            _issue(issues, "error", "COMPONENT_FIELDS_MISSING", "构件必须包含 id、level、category", entity)
        key = (component_id, level)
        if component_id and level and key in component_keys:
            _issue(issues, "error", "COMPONENT_DUPLICATE", f"同层构件重复：{component_id}", entity)
        component_keys.add(key)
        requirements = CATEGORY_REQUIREMENTS.get(category)
        if requirements is None:
            _issue(issues, "error", "COMPONENT_CATEGORY_UNSUPPORTED", f"不支持的构件类别：{category}", entity)
        else:
            measurements = component.get("measurements", {})
            if not isinstance(measurements, dict):
                _issue(issues, "error", "MEASUREMENTS_NOT_OBJECT", "measurements 必须是对象", entity)
            else:
                for field, kind in requirements.items():
                    if field not in measurements:
                        _issue(issues, "warning", "MEASUREMENT_MISSING", f"缺少量测字段：{field}", entity)
                        continue
                    try:
                        _measure(measurements[field], kind, f"{entity}.measurements.{field}")
                    except DrawingModelError as exc:
                        _issue(issues, "error", "MEASUREMENT_INVALID", str(exc), entity)
        _validate_status_and_confidence(component, issues, entity)
        source_refs = component.get("source_refs", [])
        if not isinstance(source_refs, list) or not source_refs:
            _issue(issues, "error", "SOURCE_MISSING", "构件缺少图纸来源", entity)
        else:
            for source_ref in source_refs:
                source_text = str(source_ref)
                if "/" in source_text:
                    source_drawing = source_text.split("/", 1)[0].strip()
                    if source_drawing and source_drawing not in drawing_numbers:
                        _issue(issues, "warning", "SOURCE_DRAWING_UNKNOWN", f"来源图号未登记：{source_drawing}", entity)

    for index, check in enumerate(collections["ocr_checks"], 1):
        entity = f"ocr:{check.get('id', index) if isinstance(check, dict) else index}"
        if not isinstance(check, dict):
            _issue(issues, "error", "OCR_CHECK_NOT_OBJECT", "OCR 复核记录必须是对象", entity)
            continue
        first = " ".join(str(check.get("first_read", "")).split())
        second = " ".join(str(check.get("second_read", "")).split())
        if not first or not second:
            _issue(issues, "error", "OCR_RESULT_MISSING", "OCR 两次结果均不能为空", entity)
        elif first != second:
            _issue(issues, "error", "OCR_MISMATCH", f"两次 OCR 不一致：{first!r} / {second!r}", entity)
        if not str(check.get("source_ref", "")).strip():
            _issue(issues, "warning", "OCR_SOURCE_MISSING", "OCR 复核缺少定位来源", entity)

    error_count = sum(issue["severity"] == "error" for issue in issues)
    warning_count = sum(issue["severity"] == "warning" for issue in issues)
    passed = error_count == 0 and (not strict or warning_count == 0)
    return {
        "project": data.get("project", ""),
        "strict": strict,
        "passed": passed,
        "summary": {
            "drawings": len(drawings),
            "axis_chains": len(collections["axis_chains"]),
            "elevations": len(collections["elevations"]),
            "components": len(collections["components"]),
            "errors": error_count,
            "warnings": warning_count,
        },
        "issues": issues,
    }
