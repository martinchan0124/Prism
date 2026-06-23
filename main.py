import os
import re
from Docx_Clarifier import WordDocClarify
import Prism_JSON as pjson

def main():
    # ==========================================
    # 1. 业务逻辑配置与环境初始化
    # ==========================================
    input_docx_path = "Test File/TEST SCRIPT carol-2015.docx" 
    
    if not os.path.exists(input_docx_path):
        print(f"[Fatal] 找不到输入文件: {input_docx_path}")
        return

    # 提取基础文件名与工程名
    base_name = os.path.splitext(os.path.basename(input_docx_path))[0]
    project_title = base_name.replace("TEST SCRIPT ", "").replace("-", " ").title().strip()

    # 设定输出目录
    cache_dir = "Cache"
    json_out_dir = "Prompt JSON"
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(json_out_dir, exist_ok=True)

    # ==========================================
    # 2. 文本降维与物理清洗阶段
    # ==========================================
    output_md_path = os.path.join(cache_dir, f"{base_name}_Cleaned.md")
    
    print(f"[*] 启动 Prism 核心管线...")
    print(f"[*] [阶段 1] 正在提取物理文本并降维至: {output_md_path}")
    
    clarify_success = WordDocClarify(input_docx_path, output_md_path)
    if not clarify_success:
        print("[!] 文本降维失败，管线终止。")
        return

    # ==========================================
    # 3. JSON 拓扑骨架初始化与全文遍历切分
    # ==========================================
    print(f"[*] [阶段 2] 降维成功，开始全文遍历并构建 1+n 数据拓扑...")
    
    # 1 号文件：全局状态机 SMJS，仅需初始化一次
    smjs_db = pjson.create_json_template("SMJS", project_title)
    
    # 读取清洗好的纯净 Markdown
    with open(output_md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # 按双换行物理切分所有文本块
    blocks = md_text.split('\n\n')
    
    current_scene_id = None
    current_sdjs = None
    scene_counter = 0
    shot_counter = 1
    
    # 角色名暂存器，用于解决名字与台词断层的问题
    pending_character = None 

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # 遇到新的一场戏 (Scene Heading)
        if block.startswith('# '):
            if current_sdjs:
                sdjs_out_path = os.path.join(json_out_dir, f"{project_title}_SDJS_{current_scene_id}.json")
                pjson.flush_to_disk(current_sdjs, sdjs_out_path)
                print(f"  -> {current_scene_id} 拆分完毕，已落盘。")

            scene_counter += 1
            current_scene_id = f"scene_{scene_counter}"
            current_sdjs = pjson.create_json_template("SDJS", project_title)
            
            # 【修复3】：直接提取标题，剔除换行，传入 scene_n 层级
            heading_text = block.replace('# ', '').replace('\n', ' ').strip()
            pjson.init_sdjs_scene(current_sdjs, current_scene_id, heading_text)
            
            shot_counter = 1
            pending_character = None

        # 遇到角色名 (将其挂起入暂存器)
        elif block.startswith('### '):
            pending_character = block.replace('### ', '').replace('\n', ' ').strip()

        # 遇到普通动作、括号提示或台词
        else:
            if not current_scene_id:
                continue 

            # 情况 A：台词与角色融合（强制带有冒号）
            if pending_character and block.startswith('> '):
                dialogue_text = block.replace('> ', '').replace('\n', ' ').strip()
                content_str = f"{pending_character}: {dialogue_text}"
                pending_character = None
                
                shot_id = f"shot-{shot_counter}"
                pjson.append_sdjs_shot(current_sdjs, current_scene_id, shot_id, content_str)
                shot_counter += 1
            
            # 【修复1 & 2】情况 B：异常排版容错（强制加上冒号，并剔除换行符）
            elif pending_character:
                cleaned_block = block.replace('\n', ' ').strip()
                content_str = f"{pending_character}: {cleaned_block}"
                pending_character = None
                
                shot_id = f"shot-{shot_counter}"
                pjson.append_sdjs_shot(current_sdjs, current_scene_id, shot_id, content_str)
                shot_counter += 1
                
            # 情况 C：纯粹的动作描述（启动句子级细化切割）
            else:
                sentences = re.split(r'(?<=[.!?])\s+', block)
                
                for sentence in sentences:
                    # 【修复2】：斩断所有段落内的 \n，替换为空格
                    sentence = sentence.replace('\n', ' ').strip()
                    if sentence: 
                        shot_id = f"shot-{shot_counter}"
                        pjson.append_sdjs_shot(current_sdjs, current_scene_id, shot_id, sentence)
                        shot_counter += 1


    # 循环结束后，不要忘记把最后一场戏的 SDJS 落盘
    if current_sdjs:
        sdjs_out_path = os.path.join(json_out_dir, f"{project_title}_SDJS_{current_scene_id}.json")
        pjson.flush_to_disk(current_sdjs, sdjs_out_path)
        print(f"  -> {current_scene_id} 拆分完毕，已落盘。")

    # 最后，将全局实体状态机 SMJS 落盘
    smjs_out_path = os.path.join(json_out_dir, f"{project_title}_SMJS.json")
    pjson.flush_to_disk(smjs_db, smjs_out_path)

    # ==========================================
    # 4. 流程结束统计
    # ==========================================
    print("=" * 40)
    print(f"[*] Prism 引擎处理完毕！")
    print(f"[*] 共解析了 {scene_counter} 个场景文件 (SDJS)。")
    print(f"[*] 全局状态机 (SMJS) 已同步更新。")
    print(f"[*] 所有输出已送达目录: ./{json_out_dir}/")

if __name__ == "__main__":
    main()