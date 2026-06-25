import json
import os
from openai import OpenAI
import Prism_JSON as pjson
import logging


class PrismSemanticEngine:
    def __init__(self, config_path="Config/config.json"):
        """
        初始化 AI 引擎，从 config.json 抓取配置，并从环境变量拿取最新密钥。
        """
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
            
        # 这里会自动抓取你在 .env 里刚刚更新的全新 API Key
        api_key = os.getenv(self.config["api_settings"]["api_key_env_var"])
        if not api_key:
            raise ValueError(f"未找到环境变量 {self.config['api_settings']['api_key_env']}")

        self.client = OpenAI(
            api_key=api_key,
            base_url=self.config["api_settings"]["base_url"]
        )
        self.model = self.config["model_parameters"]["model_name"]
        self.temperature = self.config["model_parameters"]["temperature"]

    def _build_context_prompt(self, sdjs_scene_db: dict, scene_id: str, shot_id: str, global_registry: dict) -> str:
        """
        核心 Prompt 工程：拼装上下文、全局注册表与软约束雷达。
        """
        # -----------------------------------------------------
        # 1. 物理挂载滑动窗口 (Sliding Window Context)
        # 自动向上追溯 4 个镜头，解决 "He", "She" 的代词崩溃问题
        # -----------------------------------------------------
        shots_dict = sdjs_scene_db.get("script_scenes", {}).get(f"{scene_id}_shots", {})
        shot_keys = list(shots_dict.keys())
        
        try:
            current_idx = shot_keys.index(shot_id)
        except ValueError:
            current_idx = 0
            
        start_idx = max(0, current_idx - 4)
        context_shots = []
        for i in range(start_idx, current_idx + 1):
            s_key = shot_keys[i]
            content = shots_dict[s_key].get("content", "")
            # 给目标镜头打上强视觉标记
            if s_key == shot_id:
                context_shots.append(f"-> [TARGET SHOT: {s_key}] {content}")
            else:
                context_shots.append(f"   [{s_key}] {content}")
                
        context_str = "\n".join(context_shots)
        target_content = shots_dict.get(shot_id, {}).get("content", "")
        registry_str = json.dumps(global_registry, indent=2, ensure_ascii=False)

        # -----------------------------------------------------
        # 2. 组装终极紧箍咒 (The Ultimate Prompt)
        # -----------------------------------------------------
        prompt = f"""
[ROLE & TASK]
You are the Prism Semantic Router, a rigid JSON conversion API. 
Your task is to extract entities and states from the TARGET SHOT and map them EXACTLY to the provided Entity Registry.

[THE GLOBAL ENTITY REGISTRY - MANDATORY MENU]
This is your absolute physical boundary. You must ONLY use the Int IDs from this dictionary.
WARNING:
1. DO NOT invent IDs.
2. DO NOT use string names (like "JACK") in your output arrays. You MUST use their Integer IDs (e.g., 1001).
3. If a character or location in the text is NOT in this registry, IGNORE THEM COMPLETELY.
{registry_str}

[SLIDING WINDOW CONTEXT]
Here is the recent timeline for reference ONLY (use this to resolve pronouns like "He" or "She"):
{context_str}

[TARGET SHOT]
Analyze the action and dialogue in THIS specific shot ONLY:
"{target_content}"

[CRITICAL ROUTING RULES]
You must construct the 'target_path' arrays exactly as below:
1. To update a Character/Location attribute: 
   ["elements_registry", "<CATEGORY>", "<ENTITY_ID>", "semantic_attributes"]
   *(Note: <CATEGORY> must be 'characters' or 'locations')*
2. To define which characters are physically present or addressed in the TARGET SHOT:
   ["script_scenes", "{scene_id}_shots", "{shot_id}", "characters"]
3. To define the Spatial_path (location ID) of the TARGET SHOT:
   ["script_scenes", "{scene_id}_shots", "{shot_id}", "Spatial_path"]

[SEMANTIC EXTRACTION RADAR]
When populating 'semantic_attributes' for a character, DO NOT be lazy. Scan the TARGET SHOT for these dimensions. ONLY create the key if explicitly mentioned (Do not invent details):
- "age": Exact age or age range.
- "clothes": Wearing apparel.
- "physical_state": Posture or physical condition.
- "mood": Emotional state.
- "action": What they are physically doing IN THIS SHOT.

[MANDATORY JSON STRUCTURE]
Every object inside your 'smjs_updates' and 'sdjs_updates' arrays MUST strictly follow this format:
{{
  "target_path": ["..."],
  "payload": ...
}}
Do NOT use the key 'value'. Use 'payload'.
If a field expects an array of IDs (like characters present), it MUST be an array of INTEGERS, not strings.
"""
        return prompt

    def process_shot(self, smjs_db: dict, sdjs_scene_db: dict, scene_id: str, shot_id: str, global_registry: dict) -> bool:
        """
        主执行干道。
        """
        prompt = self._build_context_prompt(sdjs_scene_db, scene_id, shot_id, global_registry)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a rigid JSON routing API. Output ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=self.temperature
            )
            
            ai_payload = json.loads(response.choices[0].message.content)
            
            # 宽容度解析与路由下发
            for update in ai_payload.get("smjs_updates", []):
                target_path = update.get("target_path")
                payload = update.get("payload") if "payload" in update else update.get("value")
                if target_path and payload is not None:
                    pjson.update_semantic_payload(smjs_db, target_path, payload)
                    
            for update in ai_payload.get("sdjs_updates", []):
                target_path = update.get("target_path")
                payload = update.get("payload") if "payload" in update else update.get("value")
                if target_path and payload is not None:
                    pjson.update_semantic_payload(sdjs_scene_db, target_path, payload)
                    
            logging.info(f"  ↳ 🧠 [AI 路由] {shot_id} 语义覆写完毕。")
            return True
            
        except Exception as e:
            logging.error(f"  ↳ ❌ [AI 路由] {shot_id} API 挂载失败: {e}")
            return False