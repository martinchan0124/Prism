import json
import Prism_JSON as pjson
from NLP_Scanner import PrismNLPEngine

def run_api_sandbox():
    print("=" * 50)
    print("🚀 Prism Core: NLP 前置扫描器接口沙盒测试")
    print("=" * 50)

    # 1. 初始化引擎
    try:
        nlp_engine = PrismNLPEngine()
    except OSError:
        print("[!] 模型未找到。请确保已在终端运行: python -m spacy download en_core_web_sm")
        return

    # 2. 伪造剧本干声 (包含极其混乱的大小写和格式)
    mock_md_text = """
# EXT. NYC SUBWAY STATION. APRIL 1953. NIGHT.

We descend upon the crowd, singling out a young man in coat and hat, JACK TAFT, late 20s, who weaves through the line of COMMUTERS.

JACK buys an evening paper at a newsstand and makes his way across 59th.

# INT. RITZ TOWER HOTEL. BAR/LOUNGE. NIGHT.

JACK easily finds a stool, nods to the BARTENDER and tosses him the newspaper.

THERESE, the younger of the women, turns to look at JACK.

THERESE: Jack, this is Carol Aird.

CAROL AIRD: Nice to meet you.

JACK TAFT: Likewise.
"""

    # 3. 初始化空白的 SMJS 状态机
    smjs_db = pjson.create_json_template("SMJS", "Lyra_Test_Project")

    # 4. 执行全量扫描与物理注册
    print("\n[*] 将 Markdown 干声送入 NLP 引擎进行脱水...")
    registry_map = nlp_engine.scan_and_register_entities(mock_md_text, smjs_db)

    # 5. 验证输出结构
    print("\n[验证 A] 引擎返回的 ID 速查表 (这个字典将喂给大模型防止幻觉):")
    print(json.dumps(registry_map, indent=2, ensure_ascii=False))

    print("\n[验证 B] 经过 NLP 覆写后的最终 SMJS 内存状态:")
    print(json.dumps(smjs_db, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run_api_sandbox()