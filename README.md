# Engineering-AI-Skill

面向工程识图、工程量计算与图纸复核的可审计规则库和计算引擎。

本仓库的原则是：AI 负责从图纸中提取并标注证据，Python 负责按已确认口径进行确定性计算。缺少尺寸、图纸版本、比例或计量口径时，必须输出待确认项，不能用经验值补齐。

## 当前范围

- M1：项目骨架、证据追踪模型和交付标准。
- M2：核心识图、工程量与审图规则。
- M5（首批）：土建设计净量计算引擎，覆盖面积、混凝土、砌体、装修、模板、钢筋、管线和计数项。

## 快速开始

```powershell
python scripts/calculate_takeoff.py examples/basic_takeoff.json --output outputs/basic-result.json --csv outputs/basic-summary.csv
python -m unittest discover -s tests -v
```

计算结果保存来源、状态、公式、净量和计取损耗后的量。它不是计价软件，也不替代适用合同、清单规范、定额或专业人员的签认。

详见 [架构](docs/architecture.md)、[工作流](docs/workflow.md) 和核心 skill [SKILL.md](skills/core/SKILL.md)。
