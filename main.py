import os
import re
import time
from dotenv import load_dotenv
from Docx_Clarifier import WordDocClarify
import Prism_JSON as pjson
from LLM_Semantic import PrismSemanticEngine
from NLP_Scanner import PrismNLPEngine  # [新增] 导入本地 NLP 前置扫描器

# 强制加载环境密钥
load_dotenv()

def main():
    # ==========================================
    # 1. 业务逻辑配置与环境初始化
    # ==========================================
    input_docx_path = "Test File/TEST SCRIPT carol-2015.docx" 
    
    if not os.path.exists(input_docx_path):
        print(f"[Fatal] 找不到输入文件: {input_docx_path}")
        return

    base_name = os.path.splitext(os.path.basename(input_docx_path))[0]
    project_title = base_name.replace("TEST SCRIPT ", "").replace("-", " ").title().strip()

    cache_dir = "Cache"
    json_out_dir = "Prompt JSON"
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(json_out_dir, exist_ok=True)

    # ==========================================
    # 2. 文本降维与物理清洗阶段
    # ==========================================
    output_md_path = os.path.join(cache_dir, f"{base_name}_Cleaned.md")
    
    print("=" * 50)
    print(f"[*] 启动 Prism 核心管线...")
    print(f"[*] [阶段 1] 正在提取物理文本并降维至: {output_md_path}")
    
    clarify_success = WordDocClarify(input_docx_path, output_md_path)
    if not clarify_success:
        print("[!] 文本解析失败，管线终止。")
        return

    # 读取降维后的纯文本，为后续双规扫描做准备
    with open(output_md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # ==========================================
    # [Pass 1] 全局静态解析与注册 (The Pre-Scan)
    # ==========================================
    print(f"\n[*] [阶段 2] 启动 Pass 1: 本地 NLP 全局实体预扫描...")
    smjs_db = pjson.create_json_template("SMJS", project_title)
    
    # 挂载本地 NLP 引擎，一口气抽干剧本里的所有人名和地名
    nlp_engine = PrismNLPEngine()
    global_registry = nlp_engine.scan_and_register_entities(md_text, smjs_db)

    # ==========================================
    # [Pass 2] 动态切片与 AI 渲染 (The Render Pass)
    # ==========================================
    print(f"\n[*] [阶段 3] 启动 Pass 2: 逐句生成 SDJS 并挂载 AI 效果器...")
    
    # 预热 AI 接口
    try:
        semantic_engine = PrismSemanticEngine(config_path="Config/config.json")
    except Exception as e:
        print(f"[Fatal] AI 引擎挂载失败: {e}")
        return

    blocks = md_text.split('\n\n')
    current_scene_id = None
    current_sdjs = None
    scene_counter = 0
    shot_counter = 1
    pending_character = None 

    print("=" * 50)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # [遇到场景标题] - 场记打板与文件落盘
        if block.startswith('# '):
            if current_sdjs:
                sdjs_out_path = os.path.join(json_out_dir, f"{project_title}_SDJS_{current_scene_id}.json")
                pjson.flush_to_disk(current_sdjs, sdjs_out_path)
                print(f"💾 {current_scene_id} 混缩完毕，物理落盘。")

            scene_counter += 1
            current_scene_id = f"scene_{scene_counter}"
            current_sdjs = pjson.create_json_template("SDJS", project_title)
            
            heading_text = block.replace('# ', '').replace('\n', ' ').strip()
            pjson.init_sdjs_scene(current_sdjs, current_scene_id, heading_text)
            
            shot_counter = 1
            pending_character = None
            print(f"\n🎬 场记打板: {current_scene_id} -> {heading_text}")

        # [遇到角色名] - 仅记录说话人，不再执行注册操作！
        elif block.startswith('### '):
            # Pass 1 已经把人注册过了，这里只是为了给接下来的台词拼接名字
            pending_character = block.replace('### ', '').replace('\n', ' ').strip()

        # [遇到动作或台词] - 切片并调用 AI
        else:
            if not current_scene_id:
                continue 

            shots_to_process = []

            # 对白处理
            if pending_character and block.startswith('> '):
                dialogue_text = block.replace('> ', '').replace('\n', ' ').strip()
                content_str = f"{pending_character}: {dialogue_text}"
                pending_character = None
                
                shot_id = f"shot-{shot_counter}"
                pjson.append_sdjs_shot(current_sdjs, current_scene_id, shot_id, content_str)
                shots_to_process.append(shot_id)
                shot_counter += 1
            
            # 旁白或连续对白处理
            elif pending_character:
                cleaned_block = block.replace('\n', ' ').strip()
                content_str = f"{pending_character}: {cleaned_block}"
                pending_character = None
                
                shot_id = f"shot-{shot_counter}"
                pjson.append_sdjs_shot(current_sdjs, current_scene_id, shot_id, content_str)
                shots_to_process.append(shot_id)
                shot_counter += 1
                
            # 纯动作处理 (按句号切分)
            else:
                sentences = re.split(r'(?<=[.!?])\s+', block)
                for sentence in sentences:
                    sentence = sentence.replace('\n', ' ').strip()
                    if sentence: 
                        shot_id = f"shot-{shot_counter}"
                        pjson.append_sdjs_shot(current_sdjs, current_scene_id, shot_id, sentence)
                        shots_to_process.append(shot_id)
                        shot_counter += 1

            # --- 核心 AI 效果器挂载 ---
            for s_id in shots_to_process:
                # [关键改动] 将 Pass 1 提取的 global_registry 作为紧箍咒传给大模型
                semantic_engine.process_shot(smjs_db, current_sdjs, current_scene_id, s_id, global_registry)
                time.sleep(0.5)

    # ==========================================
    # 5. 收尾与释放
    # ==========================================
    if current_sdjs:
        sdjs_out_path = os.path.join(json_out_dir, f"{project_title}_SDJS_{current_scene_id}.json")
        pjson.flush_to_disk(current_sdjs, sdjs_out_path)
        print(f"💾 {current_scene_id} 处理完毕，保存中。")

    smjs_out_path = os.path.join(json_out_dir, f"{project_title}_SMJS.json")
    pjson.flush_to_disk(smjs_db, smjs_out_path)
    print(f"💾 全局实体状态机 SMJS 处理完毕，保存中。")

    print("=" * 50)
    print(f"✅ Prism 引擎全量执行完毕！共解析 {scene_counter} 场戏。")
    print(f"📁 请前往 ./{json_out_dir}/ 查收属于你的赛博剧本宇宙！")

if __name__ == "__main__":
    main()