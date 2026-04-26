import json
import os
import random
import time
from flask import Flask, jsonify, request, Response, send_file
from flask_cors import CORS
from io import BytesIO
from mock_data import get_all_chats, get_chat, create_or_continue_chat
from file_mock_data import list_directory, get_file_content, file_exists

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


def _validate_path(path):
    """Reject paths containing '..' segments to prevent path traversal."""
    if not path:
        return False
    parts = path.replace("\\", "/").split("/")
    return ".." not in parts


@app.route("/api/files", methods=["GET"])
def list_files():
    """List directory contents."""
    path = request.args.get("path", "~")
    if not _validate_path(path):
        return jsonify({"error": "Invalid path"}), 400

    entries = list_directory(path)
    if entries is None:
        return jsonify({"error": "Directory not found"}), 404

    return jsonify({"entries": entries})


@app.route("/api/files/content", methods=["GET"])
def get_file_content_endpoint():
    """Get file content and metadata."""
    path = request.args.get("path")
    if not path:
        return jsonify({"error": "Missing required parameter: path"}), 400
    if not _validate_path(path):
        return jsonify({"error": "Invalid path"}), 400

    content = get_file_content(path)
    if content is None:
        return jsonify({"error": "File not found"}), 404

    return jsonify(content)


@app.route("/api/files/download", methods=["GET"])
def download_file():
    """Download a file as binary attachment."""
    path = request.args.get("path")
    if not path:
        return jsonify({"error": "Missing required parameter: path"}), 400
    if not _validate_path(path):
        return jsonify({"error": "Invalid path"}), 400

    if not file_exists(path):
        return jsonify({"error": "File not found"}), 404

    filename = os.path.basename(path)
    file_info = get_file_content(path)

    if file_info.get("previewable") and file_info.get("content") is not None:
        # Text files: serve actual content
        buffer = BytesIO(file_info["content"].encode("utf-8"))
    else:
        # Binary/mock files: generate placeholder content
        buffer = BytesIO(f"[Mock binary content for {filename}]".encode("utf-8"))

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/octet-stream",
    )


if __name__ == "__main__":
    app.run(port=5001, debug=True)
