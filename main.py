import os
from Docx_Clarifier import WordDocClarify
import Prism_JSON as pjson

def main():
    # ==========================================
    # 1. 业务逻辑配置与环境初始化
    # ==========================================
    # 暂时硬编码输入文件（假设你放在根目录或 Test File 文件夹下，可根据实际情况微调）
    input_docx_path = "Test File/TEST SCRIPT carol-2015.docx" 
    
    if not os.path.exists(input_docx_path):
        print(f"[Fatal] 找不到输入文件: {input_docx_path}")
        return

    # 提取基础文件名 (去除后缀) 
    # 例如: "TEST SCRIPT carol-2015"
    base_name = os.path.splitext(os.path.basename(input_docx_path))[0]
    
    # 提取工程名 (简单的字符串清洗，用于写入 JSON metadata)
    project_title = base_name.replace("TEST SCRIPT ", "").replace("-", " ").title().strip()

    # 设定输出目录
    cache_dir = "Cache"
    json_out_dir = "Prompt JSON"
    
    # 动态创建文件夹。exist_ok=True 保证了文件夹如果已存在，会直接跳过而不会报错崩溃
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
    # 3. JSON 拓扑骨架初始化与挂载阶段
    # ==========================================
    print(f"[*] [阶段 2] 降维成功，开始构建 1+n 状态机与时间线骨架...")
    
    # 初始化 1 号文件 (全局状态机 SMJS)
    smjs_db = pjson.create_json_template("SMJS", project_title)
    
    # 初始化 n 号文件 (第一场戏时间线 SDJS)
    sdjs_scene1_db = pjson.create_json_template("SDJS", project_title)
    
    # ----------------------------------------------------------------
    # [TO-DO]: 这里未来将挂载你自己的 Markdown 读取与正则硬切分循环代码。
    # 逻辑将是：读取 output_md_path -> 按 # 分切 Scene -> 按空行分切 Shot -> 塞入 JSON API
    # ----------------------------------------------------------------
    
    # 目前我们先强行调用 API 注入一条测试数据，验证整个内存到硬盘的流转是否畅通
    pjson.init_sdjs_scene(sdjs_scene1_db, "scene_1")
    pjson.append_sdjs_shot(
        sdjs_scene1_db, 
        scene_id="scene_1", 
        shot_id="shot-1", 
        raw_content="This is an automated test shot injected by main.py engine."
    )

    # ==========================================
    # 4. 物理落盘阶段
    # ==========================================
    smjs_out_path = os.path.join(json_out_dir, f"{project_title}_SMJS.json")
    sdjs_out_path = os.path.join(json_out_dir, f"{project_title}_SDJS_scene_1.json")
    
    print(f"[*] [阶段 3] 执行内存状态固化与物理落盘...")
    pjson.flush_to_disk(smjs_db, smjs_out_path)
    pjson.flush_to_disk(sdjs_scene1_db, sdjs_out_path)
    
    print("=" * 40)
    print(f"[*] Prism 管线执行完毕！")
    print(f"[*] 状态机实体数据 (SMJS) 已落盘: {smjs_out_path}")
    print(f"[*] 场景时间线数据 (SDJS) 已落盘: {sdjs_out_path}")

if __name__ == "__main__":
    main()