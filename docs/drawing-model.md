# 图纸识读模型

模型用于把图纸观察转成可校验 JSON。它不执行 OCR，也不从像素推算尺寸。

## 顶层字段

- `project`：项目名称。
- `drawings`：图纸台账，至少一项。
- `axis_chains`：轴网分段尺寸与总尺寸。
- `elevations`：可为负值的标高记录。
- `components`：房间、墙、门窗、梁板柱、基础、钢筋和安装构件。
- `ocr_checks`：同一图纸区域的两次 OCR 结果。

## 图纸台账

每张图包含 `drawing_no`、`title`、`discipline`、`revision`、`scale`、`unit`、`status`。`status` 为 `active`、`replaced` 或 `pending`；同一图号只能有一个有效版本。

## 状态与置信度

识读项的 `status` 为 `confirmed`、`inferred` 或 `pending`，`confidence` 为 `high`、`medium` 或 `low`。`inferred` 添加 `inference_note`，`pending` 添加 `pending_reason`。低置信度内容不能标为 `confirmed`。

## 构件量测字段

量测值统一写为 `{ "value": 数字, "unit": 单位 }`。长度接受 `m`、`cm`、`mm`，面积接受 `m2`、`mm2`，数量接受 `each`、`count`、`个`。

| 类别 | 必填量测字段 |
|---|---|
| `room` | `area` |
| `wall` | `length`, `height`, `thickness` |
| `door`, `window`, `opening` | `width`, `height`, `count` |
| `column` | `section_width`, `section_depth`, `storey_height`, `count` |
| `beam` | `length`, `width`, `height`, `count` |
| `slab` | `area`, `thickness` |
| `foundation` | `length`, `width`, `height`, `count` |
| `rebar` | `diameter`, `length`, `count` |
| `pipe`, `duct`, `cable` | `length` |
| `equipment` | `count` |

运行：

```powershell
python scripts/validate_drawing_model.py examples/drawing_model.json --output outputs/drawing-report.json --strict
```
