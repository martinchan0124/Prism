# Prism Core ◬

A deterministic, tree-topology screenplay parser that deconstructs unformatted legal scripts into generic object registries and atomic shot timeline graphs driven by pure integer identifiers.

## 核心理念 (Core Philosophy)

Prism 摒弃了传统自然语言处理中模糊的语义猜测，采用**“物理降维”**的硬核管线。我们将非结构化的影视剧本文本（Word/PDF）视为原始的模拟信号，通过严格的物理缩进坐标和正则表达式进行切割，最终映射为一套完全由 `Int` 整型 ID 驱动的底层 JSON 拓扑网格。

系统采用创新的 **1+n 解耦架构**，将“空间状态”与“时间动作”彻底物理隔离：
* **[1] SMJS (State Machine JSON)**: 全局实体状态机。作为唯一的物理真理标准（Single Source of Truth），负责静态存储所有 Character, Element 与 Location 的 ID 映射与动态属性。
* **[n] SDJS (Scene Data JSON)**: 场景时间线图谱。作为纯粹的事件流载荷，以原子化的 Shot 为单位，记录不同 ID 实体在时空坐标上的物理交互。

## 系统特性 (Features)

* **绝对物理边界**：利用 `python-docx` 与 `pdfplumber` 获取底层绝对坐标与缩进，彻底解决台词与动作描述的格式粘连。
* **纯净中间层**：强制产出格式极其规整的 Markdown 文件，切断所有的分页符、无关括号与排版噪点。
* **增量状态覆写**：提供专用的 API 节点寻址路由，允许后续 AI 模块对角色着装、道具归属进行非破坏性的增量融合。
* **Git 友好落盘**：输出的 JSON 严格关闭属性乱序与 ASCII 转义，保证跨版本比对（Diff）时的行级精准度。

## 快速起步 (Quick Start)

### 1. 文本降维与物理清洗
将混乱的剧本文件洗涤为规整的中间层 Markdown：

```python
from prism_core import PDFClarify, WordDocClarify

# 处理 PDF (依赖绝对坐标系)
PDFClarify("script_draft.pdf", "cleaned_script.md")

# 处理 Word (依赖相对缩进系)
WordDocClarify("script_draft.docx", "cleaned_script.md")
