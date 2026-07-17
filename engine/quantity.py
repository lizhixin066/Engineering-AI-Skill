"""Traceable, unit-safe quantity calculations for reviewed engineering inputs."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


class QuantityError(ValueError):
    """Raised when an input is incomplete, inconsistent, or not supported."""


LENGTH_FACTORS = {"m": Decimal("1"), "mm": Decimal("0.001"), "cm": Decimal("0.01")}
COUNT_FACTORS = {"each": Decimal("1"), "count": Decimal("1"), "个": Decimal("1")}
RATE_FACTORS = {"kg/m": Decimal("1")}


def _decimal(value: Any, label: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise QuantityError(f"{label} 必须为数字") from exc
    if result < 0:
        raise QuantityError(f"{label} 不得为负数")
    return result


def measure(raw: Any, kind: str, label: str) -> Decimal:
    if not isinstance(raw, dict) or set(("value", "unit")) - raw.keys():
        raise QuantityError(f"{label} 必须包含 value 和 unit")
    factors = {"length": LENGTH_FACTORS, "count": COUNT_FACTORS, "rate": RATE_FACTORS}[kind]
    unit = str(raw["unit"]).strip().lower()
    if unit not in factors:
        raise QuantityError(f"{label} 的单位 {unit!r} 不适用于 {kind}")
    return _decimal(raw["value"], label) * factors[unit]


def _required(inputs: dict[str, Any], key: str, kind: str = "length") -> Decimal:
    if key not in inputs:
        raise QuantityError(f"缺少 inputs.{key}")
    return measure(inputs[key], kind, f"inputs.{key}")


def _product(raw: dict[str, Any], keys: tuple[str, ...], prefix: str = "扣减项") -> Decimal:
    product = Decimal("1")
    for key in keys:
        if key not in raw:
            raise QuantityError(f"{prefix} 缺少 {key}")
        product *= measure(raw[key], "length", f"{prefix}.{key}")
    return product


def _deductions(options: dict[str, Any], keys: tuple[str, ...]) -> Decimal:
    raw_deductions = options.get("deductions", [])
    if not isinstance(raw_deductions, list):
        raise QuantityError("options.deductions 必须为数组")
    return sum((_product(value, keys, f"扣减项 {index}") for index, value in enumerate(raw_deductions, 1)), Decimal("0"))


def _quantity(item: dict[str, Any]) -> tuple[Decimal, Decimal, str, str]:
    item_type = item.get("type")
    inputs = item.get("inputs")
    options = item.get("options", {})
    if not isinstance(inputs, dict) or not isinstance(options, dict):
        raise QuantityError("inputs 和 options 必须是对象")

    length = lambda key: _required(inputs, key)
    if item_type == "area":
        gross = length("length") * length("width")
        net, unit, formula = gross - _deductions(options, ("length", "width")), "m2", "长度 × 宽度 − 扣减面积"
    elif item_type in {"rectangular_prism", "beam", "column"}:
        gross = length("length") * length("width") * length("height")
        net, unit, formula = gross - _deductions(options, ("length", "width", "height")), "m3", "长度 × 宽度 × 高度 − 扣减体积"
    elif item_type == "slab":
        gross = length("length") * length("width") * length("thickness")
        net, unit, formula = gross - _deductions(options, ("length", "width", "thickness")), "m3", "长度 × 宽度 × 厚度 − 洞口体积"
    elif item_type == "wall_masonry":
        gross = length("length") * length("height") * length("thickness")
        net, unit, formula = gross - _deductions(options, ("width", "height", "thickness")), "m3", "墙长 × 墙高 × 墙厚 − 洞口体积"
    elif item_type == "wall_finish":
        sides = _decimal(options.get("sides", 1), "options.sides")
        gross = length("length") * length("height") * sides
        net, unit, formula = gross - _deductions(options, ("width", "height")) * sides, "m2", "墙长 × 墙高 × 面数 − 洞口面积 × 面数"
    elif item_type == "formwork_rectangular_prism":
        l, w, h = length("length"), length("width"), length("height")
        gross = Decimal("2") * (l + w) * h
        if options.get("include_top", False):
            gross += l * w
        if options.get("include_bottom", False):
            gross += l * w
        net, unit, formula = gross, "m2", "2 × (长度 + 宽度) × 高度，按选项加顶/底面"
    elif item_type == "rebar":
        count, bar_length = _required(inputs, "count", "count"), length("length")
        if "unit_weight" in inputs:
            unit_weight = measure(inputs["unit_weight"], "rate", "inputs.unit_weight")
            rate_basis = "输入单位重"
        else:
            diameter_mm = length("diameter") * Decimal("1000")
            unit_weight, rate_basis = diameter_mm * diameter_mm / Decimal("162"), "d²/162"
        gross = count * bar_length * unit_weight
        net, unit, formula = gross, "kg", f"根数 × 单根长度 × 单位重（{rate_basis}）"
    elif item_type == "pipe":
        gross = length("length")
        net, unit, formula = gross, "m", "管道计量长度"
    elif item_type == "count":
        gross = _required(inputs, "count", "count")
        net, unit, formula = gross, "each", "直接计数"
    else:
        raise QuantityError(f"不支持的 type: {item_type!r}")

    if net < 0:
        raise QuantityError("扣减量大于毛量")
    waste = _decimal(options.get("waste_factor", 0), "options.waste_factor")
    return gross, net, unit, formula if waste == 0 else f"{formula}；净量 × (1 + 损耗率)"


def _number(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))


def calculate_document(data: dict[str, Any], strict: bool = False) -> dict[str, Any]:
    """Calculate every item and retain the audit trail in a JSON-serializable result."""
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise QuantityError("顶层必须包含 items 数组")
    results, warnings, ids = [], [], set()
    for index, item in enumerate(data["items"], 1):
        if not isinstance(item, dict):
            raise QuantityError(f"第 {index} 项必须是对象")
        item_id = str(item.get("id", "")).strip()
        if not item_id:
            raise QuantityError(f"第 {index} 项缺少 id")
        if item_id in ids:
            raise QuantityError(f"存在重复 id: {item_id}")
        ids.add(item_id)
        gross, net, unit, formula = _quantity(item)
        options = item.get("options", {})
        waste = _decimal(options.get("waste_factor", 0), "options.waste_factor")
        item_warnings = []
        if not item.get("source_refs"):
            item_warnings.append("缺少图纸/文件来源")
        status = item.get("status", "pending")
        if status not in {"confirmed", "inferred", "pending"}:
            item_warnings.append(f"未知状态 {status!r}")
        elif status != "confirmed":
            item_warnings.append(f"状态为 {status}")
        warnings.extend(f"{item_id}: {warning}" for warning in item_warnings)
        results.append({
            "id": item_id, "description": item.get("description", ""), "type": item.get("type"),
            "unit": unit, "gross_quantity": _number(gross), "net_quantity": _number(net),
            "quantity": _number(net * (Decimal("1") + waste)), "formula": formula,
            "source_refs": item.get("source_refs", []), "status": status, "warnings": item_warnings,
        })
    if strict and warnings:
        raise QuantityError("严格模式拒绝待确认或无来源项：" + "；".join(warnings))
    return {"project": data.get("project", ""), "results": results, "warnings": warnings}
