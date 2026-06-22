import os
import re
import pdfplumber

def MarkdownRefine(rawMarkdown: str) -> str:
    """
    清洗初版 Markdown 中的剧本格式残留（如 CONT'D），并修复台词与动作粘连的物理边界。
    强制拉开物理段落间距，切断分页符。
    """
    lines = rawMarkdown.split('\n')
    processed_blocks = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 把每一行都作为一个独立的物理块推入
        processed_blocks.append(line)
            
    # 用双换行（\n\n）重新连接，彻底切开台词和动作
    return "\n\n".join(processed_blocks)

def PDFClarify(inputFileDes: str, outputFileDes: str) -> bool:
    """
    清洗 PDF 剧本，利用 pdfplumber 抓取 X0 绝对物理坐标。
    将其换算为缩进尺寸后，输出带严格分类的纯净 Markdown。
    """
    if not os.path.exists(inputFileDes):
        print(f"[Error] 输入文件不存在: {inputFileDes}")
        return False
    
    try:
        cleaned_lines = []
        in_script_body = False
        
        # 匹配标准场次标题的正则表达式 (支持 EXT., INT., EXT./INT.)
        scene_heading_pattern = re.compile(r'^(EXT\./INT\.|EXT\.|INT\.)\s+[A-Z0-9].*')
        
        # 打开 PDF 物理文件
        with pdfplumber.open(inputFileDes) as pdf:
            for page in pdf.pages:
                # 抓取页面内所有文本行，并附带物理包围盒坐标
                lines = page.extract_text_lines()
                
                for line_dict in lines:
                    raw_text = line_dict['text']
                    text = raw_text.strip()
                    
                    if not text:
                        continue
                        
                    # 获取该行文本最左侧的物理绝对坐标 (x0)，并换算为英寸
                    # 1 英寸 = 72 points
                    x0_points = line_dict['x0']
                    absolute_inches = x0_points / 72.0
                    
                    # 边界闸门控制：等待第一场戏出现
                    if not in_script_body:
                        if scene_heading_pattern.match(text):
                            in_script_body = True
                        else:
                            continue
                    
                    # 边界闸门控制：撞到结尾标识直接终止所有物理读取
                    if "THE END" in text:
                        break
                        
                    # 过滤纯数字页码
                    if text.isdigit():
                        continue
                        
                    # 收缩文本内部无意义的连续大空格
                    text = re.sub(r'\s+', ' ', text)
                    
                    # 剥离各种干扰后缀，提取纯净字符串用于角色名验证
                    char_test_str = re.sub(r'\s*\([Cc][Oo][Nn][Tt][\'’]?[Dd]\)', '', text)
                    char_test_str = re.sub(r'\s*\([Cc][Oo][Nn][Tt][Ii][Nn][Uu][Ee][Dd]\)', '', char_test_str)
                    char_test_str = re.sub(r'\s*\([Vv]\.[Oo]\.\)', '', char_test_str)
                    char_test_str = re.sub(r'\s*\([Oo]\.[Ss]\.\)', '', char_test_str).strip()
                    
                    # ---------------------------------------------------------
                    # 物理绝对坐标判定网格
                    # ---------------------------------------------------------
                    
                    # 1. 场次标头 (一级标题)
                    if scene_heading_pattern.match(text):
                        cleaned_lines.append(f"\n# {text}")
                        
                    # 2. 角色名标头 (三级标题)
                    # 特征：全大写，短，不以标点结尾，绝对坐标向右偏移较多 (> 3.0 英寸)
                    elif char_test_str.isupper() and len(char_test_str) < 40 and not char_test_str.endswith(('.', '?', '!')) and absolute_inches > 3.0:
                        cleaned_lines.append(f"\n### {char_test_str}")
                        
                    # 3. 舞台指示/情绪提示 (直接保留)
                    elif text.startswith('(') and text.endswith(')'):
                        cleaned_lines.append(text)
                        
                    # 4. 台词识别 (引用块)
                    # 特征：有明显缩进，介于动作与角色名之间 (绝对坐标 > 2.0 英寸)
                    elif absolute_inches > 2.0:
                        cleaned_lines.append(f"> {text}")
                        
                    # 5. 客观动作描述 (正文)
                    # 特征：紧贴页面左侧基础边距
                    else:
                        cleaned_lines.append(text)
                        
                else:
                    # 内层循环正常结束，继续解析下一页
                    continue
                # 内层循环被 THE END 截断，直接跳出外层分页循环
                break
                
        # 组装初版 Markdown
        raw_markdown_content = "\n".join(cleaned_lines).strip()
        
        # 接入精炼过滤器，强行拉开物理段落隔离
        final_markdown_content = MarkdownRefine(raw_markdown_content)
        
        # 最终落盘输出
        with open(outputFileDes, "w", encoding="utf-8") as f:
            f.write(final_markdown_content)
            
        return True
        
    except Exception as e:
        print(f"[Exception] PDF 解析过程中发生致命错误: {str(e)}")
        return False

# ---------------------------------------------------------
# 本地调试与调用入口
# ---------------------------------------------------------
if __name__ == "__main__":
    # 替换为你实际的测试文件路径
    input_pdf_path = "Test File/Carol Test.pdf"
    output_md_path = "Carol_Cleaned_From_PDF.md"
    
    print(f"[{input_pdf_path}] 正在载入 Prism 物理坐标解析管线...")
    success = PDFClarify(input_pdf_path, output_md_path)
    
    if success:
        print(f"清洗成功！底层 Markdown 数据已落盘至: {output_md_path}")
    else:
        print("清洗中断，请检查控制台报错信息。")