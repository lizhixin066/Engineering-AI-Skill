---
name: engineering-ai-skill
description: 对建筑、结构、机电工程图纸、PDF、CAD 导出图或 IFC 资料进行可追溯的识图、工程量计算和图纸复核。用于建立图纸台账、提取轴网/标高/构件/尺寸、核验 OCR、编制土建及安装工程量计算书、输出异常与置信度、生成 CSV 或 Excel 交付时使用。
---

# 工程 AI 技能

遵循“先取证，后判断，再计算，最后复核”。图纸、有效变更、构件表和用户明确输入是事实来源；模型经验、像素量距和不完整 OCR 不是。

## 执行顺序

1. 读取 `rules/drawing_rules.md`，建立图纸台账并完成专业、版本、比例、单位、轴网和标高检查。
2. 把图纸观察写成带定位来源的结构化构件；读取 `rules/quantity_rules.md` 选择计量口径和计算规则。
3. 对已确认数据运行 `scripts/calculate_takeoff.py`。不要手算后覆盖脚本结果；若需扩展公式，在 `engine/quantity.py` 增加测试后实现。
4. 读取 `rules/review_rules.md` 进行冲突、缺失、单位、重复与数量级检查。
5. 交付图纸台账、分项计算书、汇总表、待确认项和复核报告。每行包含来源、公式、输入单位和状态。

## 强制停止条件

- 无法确定专业、图纸版本、比例/单位或关键尺寸时，标记 `pending` 并停止该项自动计算。
- 尺寸、编号、标高、材料或比例冲突时，输出冲突双方及来源，等待人工确认。
- 仅凭图像像素或模糊 OCR 得到的数据不得标为 `confirmed`。

## 资源

- [识图规则](rules/drawing_rules.md)
- [工程量规则](rules/quantity_rules.md)
- [审图规则](rules/review_rules.md)
- [计算器输入与命令](../../docs/workflow.md)
