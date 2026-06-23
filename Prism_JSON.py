import json
from typing import Dict, List, Any

# ==========================================
# 模块一：拓扑骨架初始化
# ==========================================
def create_json_template(json_type: str, project_title: str) -> Dict:
    """
    生成对应拓扑结构的空壳字典。
    json_type: "SMJS" (状态机实体数据) 或 "SDJS" (场景时间线数据)
    """
    base_template = {
        "metadata": {
            "project_title": project_title,
            "parser_architecture": "tree_topology_v1_int_id",
            "JSON Type": "Script Data" if json_type == "SMJS" else "Scene Data"
        }
    }

    if json_type == "SMJS":
        base_template["elements_registry"] = {
            "characters": {},
            "Elements": {},
            "locations": {}
        }
    elif json_type == "SDJS":
        base_template["script_scenes"] = {}
    else:
        raise ValueError(f"未知的 JSON 类型: {json_type}。仅支持 'SMJS' 或 'SDJS'。")

    return base_template


# ==========================================
# 模块二：SMJS 状态机实体注入
# ==========================================
def register_smjs_entity(db_ref: Dict, category: str, entity_id: int, raw_name: str) -> bool:
    """
    在 SMJS 数据库中注册一个新的基础实体。
    category: "characters", "Elements" 或 "locations"
    """
    if "elements_registry" not in db_ref:
        return False
        
    if category not in ["characters", "Elements", "locations"]:
        return False

    # 实体 ID 必须转换为字符串形式作为 JSON 的 key，但系统逻辑层面你依然可以用 int 对接
    entity_key = str(entity_id)
    
    db_ref["elements_registry"][category][entity_key] = {
        "raw_name": raw_name,
        "semantic_attributes": {}
    }
    return True


# ==========================================
# 模块三：SDJS 时间线物理构建
# ==========================================
def init_sdjs_scene(db_ref: Dict, scene_id: str) -> bool:
    """
    在 SDJS 中开启一个新的大场次容器。
    """
    if "script_scenes" not in db_ref:
        return False
        
    if scene_id not in db_ref["script_scenes"]:
        db_ref["script_scenes"][scene_id] = {}
        
    return True

def append_sdjs_shot(db_ref: Dict, scene_id: str, shot_id: str, raw_content: str) -> bool:
    """
    将物理文本流注入到最底层的叶子节点，并强制预留空占位符。
    """
    if "script_scenes" not in db_ref or scene_id not in db_ref["script_scenes"]:
        return False

    db_ref["script_scenes"][scene_id][shot_id] = {
        "Spatial_path": [],
        "environment": {
            "spatial": "",
            "temporal": "",
            "semantic_attributes": {}
        },
        "content": raw_content,
        "characters": [],
        "Elements": []
    }
    return True


# ==========================================
# 模块四：AI 语义特征覆写
# ==========================================
def update_semantic_payload(db_ref: Dict, target_path: List[str], payload: Any) -> bool:
    """
    通过路径数组进行精确寻址并覆写/更新载荷。
    如果路径末端是字典且 payload 是字典，则执行合并更新 (update)；
    如果路径末端是列表，或者结构不一致，则直接物理覆盖。
    """
    if not target_path:
        return False

    current_node = db_ref
    
    # 逐层下探到倒数第二个节点
    for key in target_path[:-1]:
        # 统一将 int ID 转换为 str 以适配字典键值
        key_str = str(key)
        if isinstance(current_node, dict) and key_str in current_node:
            current_node = current_node[key_str]
        else:
            # 路径断链，寻址失败
            return False

    final_key = str(target_path[-1])
    
    # 确保最终节点存在于当前层级中
    if isinstance(current_node, dict):
        if final_key in current_node and isinstance(current_node[final_key], dict) and isinstance(payload, dict):
            # 字典融合：针对 semantic_attributes 等属性的增量更新
            current_node[final_key].update(payload)
        else:
            # 直接物理覆盖：针对数组或新建键值
            current_node[final_key] = payload
        return True
        
    return False


# ==========================================
# 模块五：物理落盘
# ==========================================
def flush_to_disk(db_ref: Dict, output_filepath: str) -> bool:
    """
    将内存数据库按高可读性规范持久化输出到物理 JSON 文件。
    """
    try:
        with open(output_filepath, "w", encoding="utf-8") as f:
            json.dump(
                db_ref, 
                f, 
                indent=2, 
                ensure_ascii=False, 
                sort_keys=False
            )
        return True
    except Exception as e:
        print(f"[Error] 落盘失败: {str(e)}")
        return False