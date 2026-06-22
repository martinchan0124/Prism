import os
import re
from docx import Document
from docx.shared import Inches

def WordDocClarify(inputFileDes: str, outputFileDes: str) -> bool:
    # ... 前置检查和状态机闸门代码保持不变 ...
    try:
        doc = Document(inputFileDes)
        cleaned_lines = []
        in_script_body = False
        scene_heading_pattern = re.compile(r'^(EXT\./INT\.|EXT\.|INT\.)\s+[A-Z0-9].*')
        
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if not text: continue
            
            # ... 剧本起止闸门检查保持不变 ...
            
            # 【核心修改点】：获取当前段落的左缩进值
            # 如果是None，说明是顶格的默认排版
            left_indent = paragraph.paragraph_format.left_indent
            indent_inches = left_indent.inches if left_indent else 0.0

            text = re.sub(r'\s+', ' ', text)
            
            # 1. 场次标头
            if scene_heading_pattern.match(text):
                cleaned_lines.append(f"\n# {text}")
            
            # 2. 角色名标头 (特征：全大写，且通常有较深的缩进，比如大于 2.5 英寸)
            elif text.isupper() and len(text) < 30 and indent_inches > 2.5:
                cleaned_lines.append(f"\n## {text}")
            
            # 3. 台词解析 (特征：缩进介于动作和角色名之间，通常在 1.5 到 2.5 英寸之间)
            # 利用 Markdown 的引用块 ">" 来将其与客观动作彻底物理隔离
            elif indent_inches > 1.0 and indent_inches <= 2.5:
                cleaned_lines.append(f"> {text}")
                
            # 4. 客观动作描述 (特征：顶格或者基础缩进，小于或等于 1.0 英寸)
            else:
                cleaned_lines.append(f"{text}")
            
            # 1. 过滤掉完全为空的行
            if not text:
                continue
                
            # 2. 边界检查：检测是否进入剧本正文
            if not in_script_body:
                if scene_heading_pattern.match(text):
                    in_script_body = True  # 捕获到第一场戏，开启闸门
                else:
                    continue  # 未进入正文前，所有的标题页、奖项申报信息直接丢弃
            
            # 3. 边界检查：检测剧本是否结束
            if "THE END" in text:
                break  # 撞到结尾标识，直接终止读取，丢弃后续所有尾页冗余
                
            # 4. 物理清洗：过滤纯数字页码
            if text.isdigit():
                continue
                
            # 5. 格式规整：收缩文本内部无意义的连续大空格 (如剧本中的多空格缩进)
            text = re.sub(r'\s+', ' ', text)
            
            # 6. Markdown 标准化标记转换
            # 如果是场次标题，转换为一级标题
            if scene_heading_pattern.match(text):
                cleaned_lines.append(f"\n# {text}")
            # 如果是纯大写的角色说话名，转换为二级标题方便后续AI识别主语
            elif text.isupper() and len(text) < 30 and not text.startswith(('EXT', 'INT')):
                cleaned_lines.append(f"\n## {text}")
            # 普通动作动作描述或对白内容，保持平铺文本
            else:
                cleaned_lines.append(text)
                
        # 将清洗完毕的行组合为完整的Markdown文本
        markdown_content = "\n".join(cleaned_lines).strip()
        
        # 写入目标输出文件
        with open(outputFileDes, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        return True
        
    except Exception as e:
        print(f"[Exception] 清洗过程中发生致命错误: {str(e)}")
        return False

# ---------------------------------------------------------
# 本地调试入口 (Main函数)
# ---------------------------------------------------------
if __name__ == "__main__":
    input_word = "TEST SCRIPT carol-2015.docx"
    output_md = "Carol_Cleaned.md"
    
    print("Start to generate Clarified Markdown...")
    success = WordDocClarify(input_word, output_md)
    
    if success:
        print(f"Markdown file generated successfully and saved to: {output_md}")
    else:
        print("Failed to generate Markdown. Please check the error messages above.")

