import json
import os
import random
import time
import uuid
from flask import Flask, jsonify, make_response, request, Response, send_file
from flask_cors import CORS
from io import BytesIO
from mock_data import get_all_chats, get_chat, create_or_continue_chat
from file_mock_data import list_directory, get_file_content, file_exists

app = Flask(__name__)
CORS(app)

# --- Mock SSO State ---
MOCK_SSO_COOKIES = {}  # token -> user info
MOCK_AUTH_CODES = {}   # code -> access_token
MOCK_ACCESS_TOKENS = {} # access_token -> user info
MOCK_XAUTH_TOKENS = {}  # x-auth-token -> user info
MOCK_CLIENT_ID = "mock-client-id"
MOCK_CLIENT_SECRET = "mock-client-secret"
MOCK_TEST_USER = {
    "id": "1001",
    "name": "测试用户",
    "email": "test@example.com",
    "avatar": "",
    "username": "testuser"
}


# --- X-Auth-Token Validation ---

@app.before_request
def validate_xauth_token():
    """Validate X-Auth-Token for /api/ routes.

    If a token is provided, it must be valid.
    If no token is provided, allow through (mock data is public).
    """
    if not request.path.startswith("/api/"):
        return None

    x_auth_token = request.headers.get("X-Auth-Token", "")
    if not x_auth_token:
        # No token — allow anonymous access for mock data
        return None

    if x_auth_token not in MOCK_XAUTH_TOKENS:
        return jsonify({"error": "Invalid X-Auth-Token"}), 401

    return None


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


# --- Mock SSO Endpoints ---

@app.route("/sso/authorize", methods=["GET"])
def sso_authorize():
    """Mock SSO authorize — returns a simple HTML page with a Login button."""
    redirect_uri = request.args.get("redirect_uri", "")
    state = request.args.get("state", "")

    # Generate a mock authorization code
    code = str(uuid.uuid4())
    access_token = str(uuid.uuid4())
    MOCK_AUTH_CODES[code] = access_token
    MOCK_ACCESS_TOKENS[access_token] = MOCK_TEST_USER.copy()

    html = f"""<!DOCTYPE html>
<html><head><title>Mock SSO Login</title></head>
<body style="display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:sans-serif">
<div style="text-align:center">
<h2>Mock SSO Login</h2>
<p>User: {MOCK_TEST_USER['username']} ({MOCK_TEST_USER['email']})</p>
<form method="get" action="{redirect_uri}">
<input type="hidden" name="code" value="{code}" />
<input type="hidden" name="state" value="{state}" />
<button type="submit" style="padding:10px 24px;font-size:16px;cursor:pointer">Login</button>
</form>
</div>
</body></html>"""

    # Set SSO Cookie on parent domain (simulates real SSO behavior)
    sso_cookie = str(uuid.uuid4())
    MOCK_SSO_COOKIES[sso_cookie] = MOCK_TEST_USER.copy()
    response = make_response(html)
    response.set_cookie("sso_token", sso_cookie, domain=".localhost", path="/")
    return response


@app.route("/sso/token", methods=["POST"])
def sso_token():
    """Mock SSO token exchange — accepts authorization code, returns access_token."""
    # Support both form-encoded and JSON body
    if request.content_type and "json" in request.content_type:
        data = request.get_json(force=True)
    else:
        data = request.form.to_dict()

    code = data.get("code", "")
    client_id = data.get("client_id", "")
    client_secret = data.get("client_secret", "")

    if client_id != MOCK_CLIENT_ID or client_secret != MOCK_CLIENT_SECRET:
        return jsonify({"error": "invalid_client"}), 401

    access_token = MOCK_AUTH_CODES.pop(code, None)
    if not access_token:
        return jsonify({"error": "invalid_grant"}), 400

    return jsonify({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600
    })


@app.route("/sso/userinfo", methods=["POST"])
def sso_userinfo():
    """Mock SSO userinfo — accepts body {client_id, access_token, scope}, returns user info."""
    data = request.get_json(force=True)
    client_id = data.get("client_id", "")
    access_token = data.get("access_token", "")

    if client_id != MOCK_CLIENT_ID:
        return jsonify({"error": "invalid_client"}), 401

    user = MOCK_ACCESS_TOKENS.get(access_token)
    if not user:
        return jsonify({"error": "invalid_token"}), 401

    return jsonify(user)


@app.route("/sso/token-exchange", methods=["POST"])
def sso_token_exchange():
    """Mock token exchange — accepts SSO Cookie, returns x-auth-token."""
    cookie_header = request.headers.get("Cookie", "")
    sso_cookie = None
    for part in cookie_header.split(";"):
        part = part.strip()
        if part.startswith("sso_token="):
            sso_cookie = part[len("sso_token="):]
            break

    if not sso_cookie:
        return jsonify({"error": "no_sso_cookie"}), 401

    # Validate the SSO cookie corresponds to a known user
    user = MOCK_SSO_COOKIES.get(sso_cookie)
    if not user:
        return jsonify({"error": "invalid_sso_cookie"}), 401

    # Generate x-auth-token
    x_auth_token = str(uuid.uuid4())
    MOCK_XAUTH_TOKENS[x_auth_token] = user

    return jsonify({
        "token": x_auth_token,
        "expires_in": 259200  # 3 days
    })


if __name__ == "__main__":
    app.run(port=5001, debug=True)
