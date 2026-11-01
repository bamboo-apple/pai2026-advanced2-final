import json
from pathlib import Path
from urllib.request import Request, urlopen

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen3:1.7b"

OUTPUT_FILE = Path(__file__).resolve().parent / "motion_plan.json"

instruction = """
1）速度50 cm/sで8秒間前進する。
2）4秒かけて、その場で左に90度回転する。
3）速度50 cm/sで8秒間前進する。
4）4秒かけて、その場で左に90度回転する。
5）速度50 cm/sで8秒間前進する。
6）4秒かけて、その場で左に90度回転する。
7）速度50 cm/sで8秒間前進する。
8）4秒かけて、その場で左に90度回転する。
9）1秒間停止する。
"""

system_prompt = """
あなたはロボットの自然言語による動作指示をJSONに変換するAIです。

出力仕様：
- 最上位キーは "actions" とし、値は配列とする。
- 前進：{"type":"forward","speed":数値,"duration":数値}
- 旋回：{"type":"turn","angle_deg":数値,"duration":数値}
- 停止：{"type":"stop","duration":数値}
- 速度の単位はm/s、角度は度、時間は秒。
- 左旋回は正、右旋回は負。
- 旋回角度をラジアンや角速度に変換しない。
- 動作の順序を保持し、指示されていない動作を追加しない。
- JSON以外を出力しない。
"""

payload = {
    "model": MODEL,
    "stream": False,  # 回答を分割せず、生成完了後にまとめて受け取る。
    "think": False,  # Qwen3のThinkingモードを無効にする。
    "format": "json",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": instruction},
    ],
}

# HTTPリクエストの作成
request = Request(
    OLLAMA_URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

print("Qwen3で動作計画を生成しています...")

try:
    with urlopen(request, timeout=120) as response:
        # HTTPレスポンスからJSONを読み込む
        result = json.load(response)

    # レスポンス内の文字列を、さらにPythonの辞書に変換する
    plan = json.loads(result["message"]["content"])

    # 最低限の形式検証
    if not isinstance(plan, dict) or not isinstance(plan.get("actions"), list):
        raise ValueError("actions配列がありません。")

    allowed_fields = {
        "forward": {"type", "speed", "duration"},
        "turn": {"type", "angle_deg", "duration"},
        "stop": {"type", "duration"},
    }

    for i, action in enumerate(plan["actions"], start=1):
        if not isinstance(action, dict):
            raise ValueError(f"動作{i}がオブジェクトではありません。")

        action_type = action.get("type")
        if action_type not in allowed_fields:
            raise ValueError(f"動作{i}の種類が不正です。")

        if set(action) != allowed_fields[action_type]:
            raise ValueError(f"動作{i}の項目が不正です。")

        for key, value in action.items():
            if key == "type":
                continue
            if type(value) not in (int, float):
                raise ValueError(f"動作{i}の{key}が数値ではありません。")
            if key == "duration" and value <= 0:
                raise ValueError(f"動作{i}のdurationが不正です。")

    OUTPUT_FILE.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(plan, ensure_ascii=False, indent=2))
    print(f"\n保存しました: {OUTPUT_FILE}")

except Exception as e:
    print(f"エラー: {e}")