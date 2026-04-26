import json
import random
import time
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from mock_data import get_all_chats, get_chat, create_or_continue_chat

app = Flask(__name__)
CORS(app)


@app.route("/api/chats", methods=["GET"])
def list_chats():
    """会话列表"""
    return jsonify(get_all_chats())


@app.route("/api/chats", methods=["POST"])
def upsert_chat():
    """统一创建/继续对话"""
    body = request.get_json(force=True)
    chat_id = body.get("chat_id", "") or ""
    prompt = body.get("prompt", "")

    chat, message_id = create_or_continue_chat(chat_id, prompt)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    return jsonify({
        "chat_id": chat["id"],
        "message_id": message_id
    })


@app.route("/api/chats/<chat_id>/stream", methods=["GET"])
def stream_chat(chat_id):
    """返回 opencode NDJSON 格式流（支持 after_ts 增量过滤）"""
    chat, logs = get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    after_ts = request.args.get("after_ts", type=int)

    # 过滤日志
    if after_ts is not None:
        logs = [l for l in logs if l.get("timestamp", 0) > after_ts]

    def generate():
        for line in logs:
            yield json.dumps(line, ensure_ascii=False) + "\n"
            time.sleep(random.randint(50, 100) / 1000)

    return Response(generate(), mimetype="text/x-ndjson")


if __name__ == "__main__":
    app.run(port=5001, debug=True)
