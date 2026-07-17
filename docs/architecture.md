# 架构

```
图纸/PDF/CAD/IFC
        │  识读，保留定位证据
        ▼
结构化构件与尺寸（JSON） ──► 规则库校验 ──► 待确认/冲突清单
        │                                      │
        └────────► Python 计算引擎 ────────────┤
                         │                      │
                         ▼                      ▼
                    计算书/CSV/XLSX        审图报告
```

`skills/core` 规定 AI 的取证、决策和交付行为；`engine` 只接受已结构化的输入并进行单位一致的确定性计算；`tests` 对计算规则实行回归测试。不要把未经确认的 OCR 文本直接送入计算引擎。

## 输入与追溯

每个工程量项必须有唯一 `id`、`type`、`inputs`、`source_refs` 和 `status`。`status` 为 `confirmed`、`inferred` 或 `pending`。严格模式拒绝非 `confirmed` 项和无来源项。
