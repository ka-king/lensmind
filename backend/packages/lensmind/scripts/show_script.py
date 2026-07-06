"""展示中文剧本——不调 media API。"""
import json, re, sys
sys.path.insert(0, "backend/packages")
from dotenv import load_dotenv; load_dotenv()
from lensmind.models.factory import create_model
from lensmind.subagents.executor import execute_subagent

model = create_model("deepseek-v4-pro")

print("正在分析产品...")
analysis = execute_subagent("product_analyzer",
    "法式复古碎花连衣裙，收腰显瘦，雪纺面料，¥199，适合春夏穿搭", "", model)

print("正在创作剧本...")
script = execute_subagent("script_writer", analysis, "", model)

# 提取 JSON
m = re.search(r"```json\s*\n(.*?)\n```", script, re.DOTALL)
if not m:
    m = re.search(r"\{.*\"scenes\".*\}", script, re.DOTALL)
data = json.loads(m.group(1) if m else script)

print()
print("=" * 60)
print(f"🎬 {data.get('title', '')}")
print(f"   时长: {data.get('total_duration_sec', 0)}秒")
print("=" * 60)

for s in data.get("scenes", []):
    print(f"""
┌─ 第{s['scene_number']}镜 ─────────────────────────────
│ 时长: {s['duration_sec']}秒 | 运镜: {s['camera_motion']}
│
│ 📣 口播文案:
│   {s['narration']}
│
│ 👩 模特图 prompt:
│   {s['model_prompt'][:120]}...
│
│ 🏞 场景图 prompt:
│   {s['scene_prompt'][:120]}...
└──────────────────────────────────────────""")

print(f"\n📝 完整口播文案:\n{data.get('full_narration', '')[:800]}")
