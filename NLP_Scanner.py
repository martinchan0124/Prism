import spacy
import re
import Prism_JSON as pjson

class PrismNLPEngine:
    def __init__(self, model_size="en_core_web_sm"):
        """
        初始化：将庞大的 spaCy 语言模型加载到本地内存中。
        相当于给宿主软件挂载了一个极度耗费 RAM 的本地特征提取库。
        """
        print(f"[*] 正在向内存装载 NLP 引擎 ({model_size})...")
        self.nlp = spacy.load(model_size)

    def _normalize_name(self, name: str) -> str:
        """
        [数据清洗器] 归一化处理。
        去除首尾空格、斩断标点符号，并统一为 Title Case (首字母大写)。
        彻底解决 "JACK", "Jack", "JACK " 在系统里算三个人的 Bug。
        """
        clean_name = re.sub(r'[^A-Za-z\s]', '', name).strip()
        return clean_name.title()

    def scan_and_register_entities(self, md_text: str, smjs_db: dict, start_id: int = 1001) -> dict:
        """
        [核心干道] 全量物理特征预扫描与注册。
        """
        print("[*] 启动全量物理特征预扫描...")
        
        found_persons = set()
        
        # ---------------------------------------------------------
        # 防线 1: 正则硬提取 (捕捉台词提示符，如 "THERESE:")
        # ---------------------------------------------------------
        dialogue_pattern = re.compile(r'^([A-Z\s]+):', re.MULTILINE)
        for match in dialogue_pattern.finditer(md_text):
            raw_name = match.group(1)
            found_persons.add(self._normalize_name(raw_name))
            
        # ---------------------------------------------------------
        # 防线 2: spaCy 深度扫描 (捕捉动作描写中的人名)
        # ---------------------------------------------------------
        doc = self.nlp(md_text)
        for ent in doc.ents:
            text = ent.text
            label = ent.label_
            
            # 剧本大小写容错补丁：拦截被误认为组织的全大写单词
            if label == "ORG" and text.isupper():
                label = "PERSON"
                
            if label == "PERSON":
                found_persons.add(self._normalize_name(text))
                
        # ---------------------------------------------------------
        # 防线 3: 噪声过滤与排序
        # ---------------------------------------------------------
        # 过滤掉单字母误判、空字符串以及环境群演代称
        blacklist = {"Man", "Woman", "Boy", "Girl", "Commuters", "Late"}
        final_roster = []
        for name in found_persons:
            if len(name) > 1 and name not in blacklist:
                final_roster.append(name)
                
        final_roster.sort() # 字母序排列，强迫症福音
        
        # ---------------------------------------------------------
        # 物理注册 (注入 SMJS)
        # ---------------------------------------------------------
        character_registry = {}
        current_id = start_id
        
        print("[*] 开始向全局跳线盘 (SMJS) 注入实体 ID...")
        for name in final_roster:
            # 1. 注册到内存状态机
            pjson.register_smjs_entity(smjs_db, "characters", current_id, name)
            # 2. 存入速查表
            character_registry[name] = current_id
            print(f"  ↳ 👤 {name} -> 编入 ID: {current_id}")
            current_id += 1
            
        print(f"[*] 预扫描完成。共清洗并注册 {len(character_registry)} 个独立实体。")
        return character_registry