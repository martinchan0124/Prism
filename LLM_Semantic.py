import os
import json
from openai import OpenAI
import Prism_JSON as pjson

class PrismSemanticEngine:
    def __init__(self, config_path="Config/config.json"):
        """
        初始化引擎：加载控制台配置，读取环境变量密钥，建立长连接。
        """
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
            
        api_key_var = self.config["api_settings"]["api_key_env_var"]
        api_key = os.getenv(api_key_var)
        
        if not api_key:
            raise ValueError(f"[Fatal] 找不到 API Key。请在终端执行: export {api_key_var}='你的真实KEY'")
            
        # 借用 openai 的 SDK 连接 DeepSeek 的底层服务器
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.config["api_settings"]["base_url"]
        )

    def _build_context_prompt(self, smjs_db: dict, sdjs_scene_db: dict, scene_id: str, shot_id: str) -> str:
        """
        [上下文打包器] 将当前的物理环境和硬路由表组装成发给大模型的巨型 Prompt。
        """
        # 1. 获取干声 (要处理的短句文本)
        target_shot = sdjs_scene_db["script_scenes"][f"{scene_id}_shots"][shot_id]
        raw_content = target_shot["content"]
        scene_heading = sdjs_scene_db["script_scenes"][scene_id]

        # 2. 获取当前的实体表映射 (防幻觉装载)
        entity_snapshot = smjs_db.get("elements_registry", {})
        
# 3. 注入死板的路由表 (The Routing Rules)
        routing_rules = f"""
[CRITICAL ROUTING RULES]
You must construct the 'target_path' arrays exactly as below:
1. To update a Character/Element/Location attribute (e.g., clothes, mood): 
   ["elements_registry", "<CATEGORY>", "<ENTITY_ID>", "semantic_attributes"]
   *(Note: <CATEGORY> must be 'characters', 'Elements', or 'locations')*
2. To define which characters are in the shot:
   ["script_scenes", "{scene_id}_shots", "{shot_id}", "characters"]
3. To define which elements are in the shot:
   ["script_scenes", "{scene_id}_shots", "{shot_id}", "Elements"]
4. To define the spatial path/location ID of the shot:
   ["script_scenes", "{scene_id}_shots", "{shot_id}", "Spatial_path"]

[MANDATORY JSON STRUCTURE]
Every object inside your 'smjs_updates' and 'sdjs_updates' arrays MUST strictly follow this format:
{{
  "target_path": ["..."],
  "payload": "..." 
}}
Do NOT use the key 'value'. You MUST use the key 'payload'.
"""
        
        # 4. 组装最终任务
        task_prompt = f"""
[ENVIRONMENT]
Scene Heading: {scene_heading}
Entity Registry Snapshot: {json.dumps(entity_snapshot, ensure_ascii=False)}

[TARGET SHOT TEXT]
{raw_content}

{routing_rules}

[TASK]
Analyze the [TARGET SHOT TEXT]. Identify participating entities from the Registry Snapshot. 
Output the exact JSON payload with 'smjs_updates' and 'sdjs_updates' arrays to update the state.
"""
        return task_prompt

    def _validate_and_parse(self, response_text: str) -> dict:
        """
        [安全熔断阀门] 检查 AI 返回的到底是不是合法的 JSON。
        """
        try:
            # 暴力清理大模型可能带有的 Markdown 代码块后缀
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_text)
            
            # 基础结构校验
            if "smjs_updates" not in data or "sdjs_updates" not in data:
                print("[!] 熔断触发: AI 返回的 JSON 缺少核心根节点。")
                return None
            return data
        except json.JSONDecodeError:
            print("[!] 熔断触发: AI 返回了损坏的非规范 JSON 格式。")
            return None

    def process_shot(self, smjs_db: dict, sdjs_scene_db: dict, scene_id: str, shot_id: str) -> bool:
        """
        主执行干道：打包 -> 发送 -> 校验 -> API 路由物理覆写
        """
        print(f"[*] 正在将 {scene_id} -> {shot_id} 发送至 Prism 语义分析引擎...")
        
        # 1. 打包
        user_prompt = self._build_context_prompt(smjs_db, sdjs_scene_db, scene_id, shot_id)
        sys_prompt = self.config["prompt_templates"]["system_instruction"]
        
        # 2. 请求外部接口
        try:
            response = self.client.chat.completions.create(
                model=self.config["model_parameters"]["model_name"],
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config["model_parameters"]["temperature"],
                max_tokens=self.config["model_parameters"]["max_tokens"],
                response_format={"type": "json_object"}
            )
            raw_output = response.choices[0].message.content
            
            # 2.5. 调试输出 (可选)
            """ print("\n[DEBUG X-RAY] DeepSeek 原始返回载荷：")
            print(raw_output)
            print("==========================================\n") """
            
        except Exception as e:
            print(f"[Fatal] 接口通信失败: {str(e)}")
            return False

        # 3. 熔断校验
        ai_payload = self._validate_and_parse(raw_output)
        if not ai_payload:
            return False
            
      # 4. 执行 API 物理覆写路由
        for update in ai_payload.get("smjs_updates", []):
            target_path = update.get("target_path")
            # 兼容 AI 擅自把 payload 叫作 value 的情况
            payload = update.get("payload") if "payload" in update else update.get("value")
            if target_path and payload is not None:
                pjson.update_semantic_payload(smjs_db, target_path, payload)
                
        for update in ai_payload.get("sdjs_updates", []):
            target_path = update.get("target_path")
            payload = update.get("payload") if "payload" in update else update.get("value")
            if target_path and payload is not None:
                pjson.update_semantic_payload(sdjs_scene_db, target_path, payload)


        print(f"  -> {shot_id} 语义覆写完成！")
        return True