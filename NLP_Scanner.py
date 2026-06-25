import spacy
import re
import Prism_JSON as pjson
import logging

logging.basicConfig(level=logging.INFO)

class PrismNLPEngine:
    def __init__(self, model_size="en_core_web_sm"):
        logging.info(f"[*] 正在向内存装载 NLP 引擎 ({model_size})...")
        self.nlp = spacy.load(model_size)

    def _normalize_name(self, name: str) -> str:
        clean_name = re.sub(r'[^A-Za-z0-9\s]', '', name).strip()
        return clean_name.title()

    def _resolve_aliases(self, name_set: set) -> list:
        sorted_names = sorted(list(name_set), key=len, reverse=True)
        unique_roster = []
        for name in sorted_names:
            is_subname = False
            for accepted in unique_roster:
                if name in accepted.split():
                    is_subname = True
                    break
            if not is_subname:
                unique_roster.append(name)
        return sorted(unique_roster)

    def scan_and_register_entities(self, md_text: str, smjs_db: dict) -> dict:
        logging.info("[*] 启动全量物理特征预扫描 (Two-Pass: Pass 1)...")
        found_persons = set()
        found_locations = set()
        
        # ---------------------------------------------------------
        # 提取 Locations (扫描 # INT. / EXT. 开头的场景标题)
        # ---------------------------------------------------------
        scene_pattern = re.compile(r'^#\s*(?:INT\.|EXT\.|INT\./EXT\.)\s+(.*?)(?:\.|\s+-)', re.MULTILINE)
        for match in scene_pattern.finditer(md_text):
            loc_name = match.group(1).strip()
            found_locations.add(self._normalize_name(loc_name))

        # 去除场景标题后的纯净文本，用于提取人名
        clean_lines = [line for line in md_text.split('\n') if not line.strip().startswith('#')]
        safe_text = '\n'.join(clean_lines)

        # ---------------------------------------------------------
        # 提取 Characters (正则 + spaCy)
        # ---------------------------------------------------------
        dialogue_pattern = re.compile(r'^([A-Z\s]+):', re.MULTILINE)
        for match in dialogue_pattern.finditer(safe_text):
            found_persons.add(self._normalize_name(match.group(1)))
            
        doc = self.nlp(safe_text)
        for ent in doc.ents:
            if (ent.label_ == "ORG" and ent.text.isupper()) or ent.label_ == "PERSON":
                found_persons.add(self._normalize_name(ent.text))
                
        # 过滤与合并
        blacklist = {"Man", "Woman", "Boy", "Girl", "Int", "Ext", "Day", "Night", "Continuous"}
        filtered_persons = {name for name in found_persons if len(name) > 1 and name not in blacklist}
        final_persons = self._resolve_aliases(filtered_persons)
        
        # ---------------------------------------------------------
        # 物理注册 (注入 SMJS 并分配号段)
        # ---------------------------------------------------------
        global_registry = {"characters": {}, "locations": {}, "Elements": {}}
        
        # 注册角色 (1000 号段)
        char_id = 1001
        for name in final_persons:
            pjson.register_smjs_entity(smjs_db, "characters", char_id, name)
            global_registry["characters"][name] = char_id
            char_id += 1
            
        # 注册地点 (3000 号段)
        loc_id = 3001
        for loc in sorted(list(found_locations)):
            pjson.register_smjs_entity(smjs_db, "locations", loc_id, loc)
            global_registry["locations"][loc] = loc_id
            loc_id += 1
            
        logging.info(f"[*] 预扫描完成。共注册 {len(global_registry['characters'])} 个角色, {len(global_registry['locations'])} 个地点。")
        return global_registry