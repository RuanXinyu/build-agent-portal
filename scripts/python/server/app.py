import json
import time
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from mock_data import get_all_chats, get_chat, create_chat

app = Flask(__name__)
CORS(app)


@app.route("/api/chats", methods=["GET"])
def list_chats():
    """会话列表"""
    return jsonify(get_all_chats())


@app.route("/api/chats", methods=["POST"])
def new_chat():
    """创建会话"""
    body = request.get_json(force=True)
    prompt = body.get("message", "") or body.get("prompt", "")
    chat = create_chat(prompt)
    return jsonify(chat)


@app.route("/api/chats/<chat_id>/stream", methods=["GET"])
def stream_chat(chat_id):
    """SSE 流式返回会话的所有消息"""
    chat, messages = get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    def generate():
        for msg in messages:
            event_data = json.dumps(msg, ensure_ascii=False)
            yield f"event: message\ndata: {event_data}\n\n"
            time.sleep(0.08)  # 80ms 延迟模拟流式效果
        yield "event: done\ndata: {}\n\n"

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(port=5001, debug=True)
