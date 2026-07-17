---
name: engineering-ai-skill
description: 对建筑、结构、机电工程图纸、PDF、CAD 导出图或 IFC 资料进行可追溯的识图、工程量计算和图纸复核。用于建立图纸台账、提取轴网/标高/构件/尺寸、核验 OCR、编制土建及安装工程量计算书、输出异常与置信度、生成 CSV 或 Excel 交付时使用。
---

# 工程 AI 技能

遵循“先取证，后判断，再计算，最后复核”。图纸、有效变更、构件表和用户明确输入是事实来源；模型经验、像素量距和不完整 OCR 不是。

1. 读取 [识图规则](../core/rules/drawing_rules.md)，建立图纸台账并完成专业、版本、比例、单位、轴网和标高检查。
2. 按专业读取 [建筑识图规则](../core/rules/architecture.md) 或 [结构识图规则](../core/rules/structure.md)，把观察写入 [图纸模型](../../docs/drawing-model.md)。
3. 在仓库根目录运行 `python scripts/validate_drawing_model.py drawing-model.json --output drawing-report.json --strict`。存在错误、警告或低置信度内容时，保留问题报告并停止相关工程量计算。
4. 读取 [工程量规则](../core/rules/quantity_rules.md)，将通过校验的构件转换为算量输入，再在仓库根目录运行 `python scripts/calculate_takeoff.py input.json --output result.json --csv summary.csv --strict`。
5. 读取 [审图规则](../core/rules/review_rules.md) 进行冲突、缺失、单位、重复与数量级检查。
6. 交付图纸台账、图纸模型校验报告、分项计算书、汇总表、待确认项和复核报告。每行包含来源、公式、输入单位和状态。

若无法确定专业、图纸版本、比例/单位或关键尺寸，标记 `pending` 并停止该项自动计算。尺寸、编号、标高、材料或比例冲突时，输出冲突双方及来源，等待人工确认。不要把 OCR 原文直接当作 confirmed 数据；先记录两次识别结果并通过模型校验。
