# Prism Core 开发者文档与 API 参考手册

## 1. 核心架构与术语词典 (Glossary & Architecture)

Prism 采用非范式化的 **1+n 拓扑路由架构**。我们将非结构化的剧本视作原始声波，通过物理引擎将其“分频”并降维成绝对理性的 JSON 节点流。

### 1.1 核心缩写与术语
* **Prism**: 本工程的核心代号。意为“棱镜”，指代系统将混乱排版的剧本文本精准折射、分离为原子化数据的物理特性。
* **1+n 架构**: 剧本数据的物理分离机制。将剧本切分为 `1` 个存放静态属性的全局状态机，和 `n` 个装载动态事件的时间线文件。
* **SMJS (State Machine JSON)**: 即 1 号文件。它是全局实体映射的“跳线盘（Patchbay）”，负责在内存中常驻所有角色（Character）、道具（Element）和空间（Location）的 `int` ID 与属性状态。相当于混音台上的通道条（Channel Strip）。
* **SDJS (Scene Data JSON)**: 即 n 号文件。以独立场次为单位切分的时间线文件。它不存储任何实体的具体细节，只记录随时间推进的动作描述以及参与该动作的 ID。相当于工程里的自动化轨（Automation Track）。
* **Shot**: 最小物理单位（镜头节点）。Prism 将自然语言里的每一段带有姓名的对白，或每一个被句号切分的纯动作短句，强行封装为一个极简的 Shot 叶子节点。
* **Buffer (暂存器)**: 清洗引擎中用于解决剧本排版粘连的机制，用于临时挂起 `#` 标题或 `###` 角色名，直到捕获到对应的正文内容后再进行合成。

---

## 2. 数据结构规范 (Schema Definition)

### 2.1 SDJS 层级规范 (Scene Data)
在最新的迭代中，SDJS 采用了**元数据与镜头流双轨制**。场次的环境描述直接挂载于外层，避免了内部节点的冗余。

```json
{
  "metadata": {
    "project_title": "Lyra",
    "parser_architecture": "tree_topology_v1_int_id",
    "JSON Type": "Scene Data"
  },
  "script_scenes": {
    "scene_1": "INT. RITZ TOWER HOTEL. BAR/LOUNGE. NIGHT.",
    "scene_1_shots": {
      "shot-1": {
        "Spatial_path": [],
        "environment": {
          "spatial": "",
          "temporal": "",
          "semantic_attributes": {}
        },
        "content": "JACK: Therese? Is that you?",
        "characters": [],
        "Elements": []
      }
    }
  }
}
```

### 3. Prism_JSON 核心 API 参考 (API Reference)

该模块是 Prism 的底层数据引擎。所有针对 `db_ref` 的操作均为**引用传递（Pass by Reference）**，直接修改内存以换取极致的 I/O 效率。

#### 3.1 骨架生命周期管理

* **`create_json_template(json_type: str, project_title: str) -> dict`**
    * **功能描述**：生成标准拓扑结构的空壳字典。
    * **`json_type`**：限制为 `"SMJS"` 或 `"SDJS"`。引擎会据此动态生成不同的内部挂载点。
    * **`project_title`**：注入到 Metadata 中的工程名。
    * **返回**：准备好装载数据的 Python `dict`。

* **`flush_to_disk(db_ref: dict, output_filepath: str) -> bool`**
    * **功能描述**：将内存状态固化为硬盘上的 `.json` 文件。
    * **机制**：强制关闭 `ensure_ascii`，关闭键名重排，严格锁定 2 空格缩进，确保输出结果对 Git 的 Diff 工具绝对友好。

#### 3.2 实体路由注册 (SMJS 专用)

* **`register_smjs_entity(db_ref: dict, category: str, entity_id: int, raw_name: str) -> bool`**
    * **功能描述**：在全局跳线盘上开辟新的实体通道。
    * **`category`**：限定词，仅支持 `"characters"`, `"Elements"`, `"locations"`。
    * **`entity_id`**：纯整数 ID（如 1001），在底层会被转化为字符串键值映射。
    * **`raw_name`**：文本中提取的原始明文。

#### 3.3 时间线注入 (SDJS 专用)

* **`init_sdjs_scene(db_ref: dict, scene_id: str, heading_text: str) -> bool`**
    * **功能描述**：初始化单个场次的时间线。
    * **机制**：构建双轨层级。将 `heading_text` 直接挂载于 `scene_id`，并自动生成对应的 `scene_n_shots` 容器，用于后续承接 Shot 节点。

* **`append_sdjs_shot(db_ref: dict, scene_id: str, shot_id: str, raw_content: str) -> bool`**
    * **功能描述**：向指定场次的叶子节点注入剥离了所有脏格式（如 `\n`）的纯净物理短句。
    * **机制**：在注入 `raw_content` 的同时，强制生成结构为空的 `Spatial_path` 数组及各类载荷列表，为 AI 语义引擎提供预留好的标准化填空卡槽。

#### 3.4 语义覆写网关 (AI 交互专用)

* **`update_semantic_payload(db_ref: dict, target_path: list, payload: any) -> bool`**
    * **功能描述**：泛用型底层状态覆写接头，允许 AI 通过绝对路径直接修改属性。
    * **`target_path`**：寻址路径数组，例如 `['elements_registry', 'characters', '1001', 'semantic_attributes']`。
    * **`payload`**：传入的修改载荷。
    * **融合保护机制**：若寻址终点为 `dict` 且载荷亦为 `dict`（如追加衣物属性），引擎将执行无损增量融合（`update`）；若为 `list`（如空间动线更新），则执行物理覆盖。

---

### 4. 物理降维管线 (Clarifier Pipeline)

位于 `Docx_Clarifier.py` 与 `PDF_Clarifier.py` 中的解析引擎，专门对付极不规范的原始剧本媒介。

* **`WordDocClarify(inputFileDes: str, outputFileDes: str) -> bool`**
    * **工作流**：探测 `.docx` 底层 XML，提取段落相对左缩进（`left_indent`）以及首行空格补偿，以此丈量文本层级。

* **`PDFClarify(inputFileDes: str, outputFileDes: str) -> bool`**
    * **工作流**：介入 PDF 绝对页面体系，抓取每一行文本的 `x0` 包围盒绝对物理坐标，并将其换算为英寸（1 英寸 = 72 pt）来切割版面。

* **`MarkdownRefine(rawMarkdown: str) -> str`**
    * **工作流**：嵌套在降维管线末端的精密过滤器。利用零宽断言与正则，物理抹杀 `(CONT'D)`、`(V.O.)` 等分页与影视工业残留，强制使用双换行确保台词与动作描述的彻底隔离。