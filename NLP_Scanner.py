import spacy
import re
import Prism_JSON as pjson

class PrismNLPEngine:
    def __init__(self, model_size="en_core_web_sm"):
        """
        初始化：将庞大的 spaCy 语言模型加载到本地内存中。
        """
        print(f"[*] 正在向内存装载 NLP 引擎 ({model_size})...")
        self.nlp = spacy.load(model_size)

    def _normalize_name(self, name: str) -> str:
        """
        [数据清洗器] 归一化处理。
        去除首尾空格、斩断标点符号，并统一为 Title Case。
        """
        clean_name = re.sub(r'[^A-Za-z\s]', '', name).strip()
        return clean_name.title()

    def _resolve_aliases(self, name_set: set) -> list:
        """
        [身份合并引擎] 共指消解。
        将 'Jack' 自动合并至 'Jack Taft' 之下，避免实体分身。
        """
        # 按名字长度从长到短排序
        sorted_names = sorted(list(name_set), key=len, reverse=True)
        unique_roster = []
        
        for name in sorted_names:
            is_subname = False
            for accepted in unique_roster:
                # 如果短名（如 Jack）完整存在于已采纳的长名中（如 Jack Taft）
                if name in accepted.split():
                    is_subname = True
                    break
            if not is_subname:
                unique_roster.append(name)
                
        return sorted(unique_roster)

    def scan_and_register_entities(self, md_text: str, smjs_db: dict, start_id: int = 1001) -> dict:
        """
        [核心干道] 全量物理特征预扫描与注册。
        """
        print("[*] 启动全量物理特征预扫描...")
        found_persons = set()
        
        # ---------------------------------------------------------
        # 防线 0: 物理隔离场景标题 (Scene Headings)
        # ---------------------------------------------------------
        # 直接屏蔽掉以 '#' 开头的环境描述，杜绝 INT/EXT/酒店名 污染人事档案
        clean_lines = []
        for line in md_text.split('\n'):
            if line.strip().startswith('#'):
                continue 
            clean_lines.append(line)
        safe_text = '\n'.join(clean_lines)

        # ---------------------------------------------------------
        # 防线 1: 正则硬提取 (捕捉台词提示符)
        # ---------------------------------------------------------
        dialogue_pattern = re.compile(r'^([A-Z\s]+):', re.MULTILINE)
        for match in dialogue_pattern.finditer(safe_text):
            raw_name = match.group(1)
            found_persons.add(self._normalize_name(raw_name))
            
        # ---------------------------------------------------------
        # 防线 2: spaCy 深度扫描
        # ---------------------------------------------------------
        doc = self.nlp(safe_text)
        for ent in doc.ents:
            text = ent.text
            label = ent.label_
            
            # 剧本大小写容错补丁
            if label == "ORG" and text.isupper():
                label = "PERSON"
                
            if label == "PERSON":
                found_persons.add(self._normalize_name(text))
                
        # ---------------------------------------------------------
        # 防线 3: 噪声过滤与剧本工业废料黑名单
        # ---------------------------------------------------------
        blacklist = {
            "Man", "Woman", "Boy", "Girl", "Commuters", "Late", 
            "Int", "Ext", "Day", "Night", "Continuous", "Os", "Vo", 
            "Barlounge", "Lounge", "Bar"
        }
        filtered_names = set()
        for name in found_persons:
            if len(name) > 1 and name not in blacklist:
                filtered_names.add(name)

        # ---------------------------------------------------------
        # 防线 4: 身份合并 (核心修复点)
        # ---------------------------------------------------------
        final_roster = self._resolve_aliases(filtered_names)
        
        # ---------------------------------------------------------
        # 物理注册 (注入 SMJS)
        # ---------------------------------------------------------
        character_registry = {}
        current_id = start_id
        
        print("[*] 开始向全局跳线盘 (SMJS) 注入实体 ID...")
        for name in final_roster:
            pjson.register_smjs_entity(smjs_db, "characters", current_id, name)
            character_registry[name] = current_id
            print(f"  ↳ 👤 {name} -> 编入 ID: {current_id}")
            current_id += 1
            
        print(f"[*] 预扫描完成。共清洗并注册 {len(character_registry)} 个独立实体。")
        return character_registry