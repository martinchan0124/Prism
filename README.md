# 🌈 Prism Core ◬ ✨

![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![Architecture](https://img.shields.io/badge/Architecture-1%2Bn_Topology-ff69b4?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Magic_in_Progress-yellow?style=for-the-badge)

> 🎬 **A deterministic, tree-topology screenplay parser.** 
> 拒绝玄学语义猜测！把混乱的剧本文本，降维打击成由纯整型 `Int ID` 驱动的底层 JSON 宇宙！🌌

---

## ✨ 核心理念 (Core Philosophy)

当非结构化的 Word/PDF 剧本像一团乱麻一样砸过来时，**Prism ◬** 就是你的终极分频器！🎛️
我们不猜语义，我们只用**物理尺子**（绝对坐标与缩进）去丈量文本，将文字转化为极其干净的 Markdown，再重构为具有强迫症般整洁的 1+n 解耦架构！

### 🎭 独家 1+n 物理隔离架构
就像 Pro Tools 里的通道条和自动化轨，我们将“状态”与“时间”彻底剥离：
* **[1] 🗂️ SMJS (State Machine JSON)**: 你的全局实体跳线盘！静态驻留所有的角色 (Characters)、道具 (Elements) 和空间 (Locations)。
* **[n] 🎞️ SDJS (Scene Data JSON)**: 你的场景时间线！以原子化的 `Shot` 🎬 为单位，纯粹记录时间流逝和实体交互，不带一丝冗余！

---

## 🚀 闪光特性 (Features)

* 📏 **物理边界丈量**：不管编剧狂敲空格还是乱用缩进，底层 `x0` 坐标和正则零宽断言教它做人！
* 🧼 **极致纯净中间层**：自动斩断 `(CONT'D)`、`(V.O.)` 等工业废料垃圾，还你一个物理隔离的完美 Markdown！
* 🧩 **AI 填空友好**：自动生成 `Spatial_path` 和 `semantic_attributes` 的空卡槽，后续大模型接入直接变身无情填表机器 🤖。
* 💾 **Git 强迫症福音**：输出的 JSON 严格锁定 2 空格缩进，关闭 ASCII 转义，跨版本 Diff 看起来比看剧本还爽！

---

## 🛠️ 快速入门 (Quick Start)

### 📦 1. 召唤依赖精灵
我们需要两个小助手来解析底层的文档魔法：
```bash
pip install python-docx pdfplumber
```

### 🪄 2. 文本降维打击 (Clarifier Pipeline)
把脏兮兮的剧本扔进去，洗出白白胖胖的中间层 MD：

```python 
from Docx_Clarifier import WordDocClarify
from PDF_Clarifier import PDFClarify

# 📄 如果是 PDF 魔法书 (依赖绝对坐标系)
PDFClarify("script_draft.pdf", "Cache/cleaned_script.md")

# 📝 如果是 Word 卷轴 (依赖相对缩进系)
WordDocClarify("script_draft.docx", "Cache/cleaned_script.md")
```

### 🧬 3. 编织 JSON 拓扑网格
调用 Prism 的底层引擎，感受内存级路由的丝滑：

```python
import Prism_JSON as pjson

# 🌟 创造世界！(初始化 1 号状态机 & n 号第一场戏)
smjs_db = pjson.create_json_template("SMJS", "My_Awesome_Project")
sdjs_scene1 = pjson.create_json_template("SDJS", "My_Awesome_Project")

# 👤 注册你的主角到全局跳线盘
pjson.register_smjs_entity(smjs_db, "characters", 1001, "JACK")

# 🎬 场记打板！记录第一场戏的第一个镜头
pjson.init_sdjs_scene(sdjs_scene1, "scene_1", "INT. BAR - NIGHT")
pjson.append_sdjs_shot(sdjs_scene1, "scene_1", "shot-1", "JACK: Make it a double, would you?")

# 💾 物理落盘，生成艺术品般的 JSON！
pjson.flush_to_disk(smjs_db, "Prompt JSON/SMJS_Registry.json")
pjson.flush_to_disk(sdjs_scene1, "Prompt JSON/SDJS_Scene_1.json")
```

## 📚 开发者秘籍 (Documentation)
迷路了吗？别慌！详细的 API 接口定义、路由规则和 JSON Schema 结构规范，全部收录在我们的硬核手册里：

####  👉 点击[查阅 Prism Core API 开发者文档](Doc/Doc.md) 📖


#### 💖 Made with Love & Logic
##### “May your scripts be flawless and your JSONs perfectly indented.” 🥂