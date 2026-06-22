import os
import re
from docx import Document

def MarkdownRefine(rawMarkdown: str) -> str:
    """
    清洗初版 Markdown，强制拉开物理段落间距。
    (因为 CONT'D 的斩断逻辑已经前置到了主循环里，这里只负责物理排版)
    """
    lines = rawMarkdown.split('\n')
    processed_blocks = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        processed_blocks.append(line)
            
    # 用双换行（\n\n）重新连接，彻底切开台词和动作
    return "\n\n".join(processed_blocks)


def WordDocClarify(inputFileDes: str, outputFileDes: str) -> bool:
    """
    清洗Word剧本，利用混合文本特征识别台词与动作，输出带严格分类的纯净Markdown。
    """
    if not os.path.exists(inputFileDes):
        print(f"[Error] 输入文件不存在: {inputFileDes}")
        return False
    
    try:
        doc = Document(inputFileDes)
        cleaned_lines = []
        
        in_script_body = False
        scene_heading_pattern = re.compile(r'^(EXT\./INT\.|EXT\.|INT\.)\s+[A-Z0-9].*')
        
        for paragraph in doc.paragraphs:
            raw_text = paragraph.text
            text = raw_text.strip()
            
            if not text:
                continue
                
            # 【关键修复】：计算混合有效缩进 (真实缩进 + 空格补偿)
            left_indent = paragraph.paragraph_format.left_indent
            indent_inches = left_indent.inches if left_indent else 0.0
            # 计算字符串开头的空格数量，每 5 个空格约等于 0.5 英寸
            leading_spaces = len(raw_text) - len(raw_text.lstrip())
            effective_indent = indent_inches + (leading_spaces * 0.1)
                
            # 闸门控制
            if not in_script_body:
                if scene_heading_pattern.match(text):
                    in_script_body = True
                else:
                    continue
            
            if "THE END" in text:
                break
            if text.isdigit():
                continue
                
            text = re.sub(r'\s+', ' ', text)
            
            # 【关键修复】：剥离各种后缀，提取最纯净的测试字符串，用于判定角色名
            char_test_str = re.sub(r'\s*\([Cc][Oo][Nn][Tt][\'’]?[Dd]\)', '', text)
            char_test_str = re.sub(r'\s*\([Cc][Oo][Nn][Tt][Ii][Nn][Uu][Ee][Dd]\)', '', char_test_str)
            char_test_str = re.sub(r'\s*\([Vv]\.[Oo]\.\)', '', char_test_str)
            char_test_str = re.sub(r'\s*\([Oo]\.[Ss]\.\)', '', char_test_str).strip()
            
            # 1. 场次标头 (一级标题)
            if scene_heading_pattern.match(text):
                cleaned_lines.append(f"\n# {text}")
                
            # 2. 角色名标头 (三级标题：全大写，长度短，且不以句号/问号结尾以防误判大写动作行)
            elif char_test_str.isupper() and len(char_test_str) < 40 and not char_test_str.endswith(('.', '?', '!')):
                cleaned_lines.append(f"\n### {char_test_str}")
                
            # 3. 括号动作/舞台指示 (例如: (to JACK) )
            elif text.startswith('(') and text.endswith(')'):
                cleaned_lines.append(text)
                
            # 4. 台词识别 (只要有效缩进超过 1.0 英寸，统统视为台词)
            elif effective_indent > 1.0:
                cleaned_lines.append(f"> {text}")
                
            # 5. 客观动作描述 (有效缩进 <= 1.0 英寸的正文)
            else:
                cleaned_lines.append(text)
                
        # 组装初版 Markdown
        raw_markdown_content = "\n".join(cleaned_lines).strip()
        
        # 接入二次精炼过滤器，强制拉开物理段落间距
        final_markdown_content = MarkdownRefine(raw_markdown_content)
        
        # 最终落盘
        with open(outputFileDes, "w", encoding="utf-8") as f:
            f.write(final_markdown_content)
            
        return True
        
    except Exception as e:
        print(f"[Exception] 清洗过程中发生致命错误: {str(e)}")
        return False

if __name__ == "__main__":
    input_word = "Test File/TEST SCRIPT carol-2015.docx"
    output_md = "Cache/Carol_Cleaned 03.md"
    WordDocClarify(input_word, output_md)