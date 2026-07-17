# 计算器输入格式

顶层 JSON 由可选的 `project` 和必填 `items` 数组组成。每项需要 `id`、`type`、`inputs`、`source_refs`、`status`。长度输入为 `{ "value": 数字, "unit": "m|mm|cm" }`；计数单位为 `each`、`count` 或 `个`；钢筋自定义单位重使用 `kg/m`。

```json
{
  "project": "示例工程",
  "items": [{
    "id": "S-SLAB-001",
    "type": "slab",
    "description": "一层板",
    "source_refs": ["S-101/轴1-4/A-C"],
    "status": "confirmed",
    "inputs": {
      "length": {"value": 7200, "unit": "mm"},
      "width": {"value": 4800, "unit": "mm"},
      "thickness": {"value": 120, "unit": "mm"}
    },
    "options": {
      "deductions": [{
        "length": {"value": 800, "unit": "mm"},
        "width": {"value": 800, "unit": "mm"},
        "thickness": {"value": 120, "unit": "mm"}
      }]
    }
  }]
}
```

支持 `area`、`rectangular_prism`、`beam`、`column`、`slab`、`wall_masonry`、`wall_finish`、`formwork_rectangular_prism`、`rebar`、`pipe` 和 `count`。砌体洞口输入为 `width`、`height`、`thickness`；墙面装修洞口为 `width`、`height`。`waste_factor` 仅在项目口径明确时添加。
