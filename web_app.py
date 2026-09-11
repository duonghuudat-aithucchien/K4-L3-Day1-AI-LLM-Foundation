"""
Web App Chatbot Trợ Lý AI - K4 Day 1
Chạy bằng thư viện chuẩn của Python (không cần cài thêm thư viện web nào).
Khởi động:
    python web_app.py
Truy cập:
    http://localhost:8000
"""

import json
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from dotenv import load_dotenv

load_dotenv()

# Import các hàm và hằng số từ template.py
from template import (
    OPENAI_MODEL,
    OPENAI_MINI_MODEL,
    PRICING_PER_1K_TOKENS,
    count_tokens,
    estimate_cost,
    retry_with_backoff,
)

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Assistant - K4 LLM Foundation</title>
    <style>
        :root {
            --bg-primary: #121826;
            --bg-secondary: #1a2234;
            --bg-card: #232d42;
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --border: #374151;
            --user-bubble: #1e3a8a;
            --assistant-bubble: #1f2937;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-main);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        /* Sidebar */
        aside {
            width: 320px;
            background-color: var(--bg-secondary);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 20px;
            gap: 16px;
        }
        aside h2 { font-size: 1.1rem; color: #60a5fa; display: flex; align-items: center; gap: 8px; }
        .form-group { display: flex; flex-direction: column; gap: 6px; }
        label { font-size: 0.82rem; font-weight: 600; color: var(--text-muted); }
        select, textarea, input {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-main);
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 0.88rem;
            outline: none;
        }
        select:focus, textarea:focus, input:focus { border-color: var(--accent); }
        textarea { resize: vertical; min-height: 80px; font-family: inherit; }
        .stats-box {
            margin-top: auto;
            background-color: var(--bg-card);
            border-radius: 10px;
            padding: 14px;
            border: 1px solid var(--border);
        }
        .stats-box h3 { font-size: 0.85rem; color: #93c5fd; margin-bottom: 8px; }
        .stat-row { display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 4px; }
        .stat-val { font-weight: 700; color: #34d399; }
        .btn-reset {
            background: transparent;
            border: 1px solid var(--border);
            color: #ef4444;
            padding: 8px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s;
        }
        .btn-reset:hover { background: rgba(239, 68, 68, 0.1); border-color: #ef4444; }

        /* Main Chat Area */
        main {
            flex: 1;
            display: flex;
            flex-direction: column;
            background-color: var(--bg-primary);
        }
        header {
            padding: 16px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        header h1 { font-size: 1.1rem; }
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .msg {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 12px;
            line-height: 1.5;
            font-size: 0.95rem;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .msg.user {
            align-self: flex-end;
            background-color: var(--user-bubble);
            border-bottom-right-radius: 2px;
        }
        .msg.assistant {
            align-self: flex-start;
            background-color: var(--assistant-bubble);
            border-bottom-left-radius: 2px;
            border: 1px solid var(--border);
        }
        .input-area {
            padding: 16px 24px;
            background-color: var(--bg-secondary);
            border-top: 1px solid var(--border);
            display: flex;
            gap: 12px;
        }
        .input-area input {
            flex: 1;
            padding: 12px 16px;
            font-size: 0.95rem;
            border-radius: 24px;
        }
        .btn-send {
            background-color: var(--accent);
            color: white;
            border: none;
            border-radius: 24px;
            padding: 0 24px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        .btn-send:hover { background-color: var(--accent-hover); }
        .btn-send:disabled { background-color: #4b5563; cursor: not-allowed; }
    </style>
</head>
<body>
    <aside>
        <h2>🤖 Cấu Hình Trợ Lý</h2>
        
        <div class="form-group">
            <label>Model LLM</label>
            <select id="modelSelect">
                <option value="gpt-4o" selected>GPT-4o (Mạnh mẽ, đa năng)</option>
                <option value="gpt-4o-mini">GPT-4o-mini (Nhanh & Rẻ)</option>
            </select>
        </div>

        <div class="form-group">
            <label>Persona (System Prompt)</label>
            <textarea id="personaInput">Bạn là trợ giảng lập trình AI thân thiện và kiên nhẫn. Luôn trả lời ngắn gọn (dưới 150 từ), giải thích bằng tiếng Việt tự nhiên và cung cấp ví dụ code minh họa tối giản khi giải thích khái niệm.</textarea>
        </div>

        <div class="form-group">
            <label>Temperature (Độ sáng tạo): <span id="tempVal">0.7</span></label>
            <input type="range" id="tempInput" min="0.0" max="1.5" step="0.1" value="0.7" oninput="document.getElementById('tempVal').innerText = this.value">
        </div>

        <button class="btn-reset" onclick="resetChat()">🗑️ Xóa Lịch Sử Hội Thoại</button>

        <div class="stats-box">
            <h3>📊 Thống Kê Phiên Chat</h3>
            <div class="stat-row"><span>Số lượt chat:</span><span class="stat-val" id="statTurns">0</span></div>
            <div class="stat-row"><span>Tổng Tokens:</span><span class="stat-val" id="statTokens">0</span></div>
            <div class="stat-row"><span>Tổng Chi Phí ($):</span><span class="stat-val" id="statCost">$0.0000</span></div>
            <div class="stat-row"><span>Quy đổi (VNĐ):</span><span class="stat-val" id="statVnd">~0 đ</span></div>
        </div>
    </aside>

    <main>
        <header>
            <h1>Trợ Lý Hội Thoại Thông Minh (K4 - Day 1)</h1>
            <span style="font-size: 0.8rem; color: #10b981;">● Sẵn sàng kết nối</span>
        </header>

        <div class="chat-container" id="chatBox">
            <div class="msg assistant">Xin chào! Mình là trợ lý AI. Hãy đặt câu hỏi bất kỳ để bắt đầu cuộc trò chuyện nhé!</div>
        </div>

        <div class="input-area">
            <input type="text" id="userInput" placeholder="Nhập câu hỏi tại đây... (Nhấn Enter để gửi)" onkeydown="if(event.key==='Enter') sendMessage()">
            <button class="btn-send" id="sendBtn" onclick="sendMessage()">Gửi</button>
        </div>
    </main>

    <script>
        let history = [];
        let totalTokens = 0;
        let totalCost = 0.0;
        let numTurns = 0;

        function updateStats(tokens, cost) {
            numTurns += 1;
            totalTokens += tokens;
            totalCost += cost;
            document.getElementById('statTurns').innerText = numTurns;
            document.getElementById('statTokens').innerText = totalTokens;
            document.getElementById('statCost').innerText = '$' + totalCost.toFixed(5);
            document.getElementById('statVnd').innerText = '~' + Math.round(totalCost * 25500) + ' đ';
        }

        function resetChat() {
            history = [];
            document.getElementById('chatBox').innerHTML = '<div class="msg assistant">Đã làm mới cuộc trò chuyện. Hãy nhập câu hỏi mới!</div>';
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();
            if (!text) return;

            const sendBtn = document.getElementById('sendBtn');
            const chatBox = document.getElementById('chatBox');
            const model = document.getElementById('modelSelect').value;
            const persona = document.getElementById('personaInput').value;
            const temperature = parseFloat(document.getElementById('tempInput').value);

            // Append user message
            const userDiv = document.createElement('div');
            userDiv.className = 'msg user';
            userDiv.innerText = text;
            chatBox.appendChild(userDiv);
            input.value = '';
            sendBtn.disabled = true;

            // Assistant placeholder
            const assistDiv = document.createElement('div');
            assistDiv.className = 'msg assistant';
            assistDiv.innerText = 'Đang suy nghĩ...';
            chatBox.appendChild(assistDiv);
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: text,
                        history: history,
                        model: model,
                        persona: persona,
                        temperature: temperature
                    })
                });

                const reader = response.body.getReader();
                const decoder = new TextDecoder('utf-8');
                let fullReply = '';
                assistDiv.innerText = '';
                let buffer = '';
                let isDone = false;

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop(); // Giữ lại phần chưa hoàn thành nếu chunk bị cắt

                    for (const line of lines) {
                        const trimmed = line.trim();
                        if (trimmed.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(trimmed.slice(6));
                                if (data.delta) {
                                    fullReply += data.delta;
                                    assistDiv.innerText = fullReply;
                                    chatBox.scrollTop = chatBox.scrollHeight;
                                }
                                if (data.done) {
                                    history.push({ role: 'user', content: text });
                                    history.push({ role: 'assistant', content: fullReply });
                                    if (history.length > 6) history = history.slice(-6);
                                    updateStats(data.tokens, data.cost);
                                    isDone = true;
                                    break;
                                }
                            } catch (e) {
                                console.error("Lỗi parse SSE:", e);
                            }
                        }
                    }
                    if (isDone) {
                        await reader.cancel();
                        break;
                    }
                }
            } catch (err) {
                assistDiv.innerText = 'Lỗi kết nối: ' + err.message;
            } finally {
                sendBtn.disabled = false;
                input.focus();
            }
        }
    </script>
</body>
</html>
"""


class ChatServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            req = json.loads(body.decode("utf-8"))

            user_msg = req.get("message", "")
            print(f"\n[Server] Nhận câu hỏi từ Web: '{user_msg}'")
            raw_history = req.get("history", [])
            model = req.get("model", OPENAI_MODEL)
            persona = req.get("persona", "Bạn là trợ lý thân thiện.")
            temperature = float(req.get("temperature", 0.7))

            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            clean_history = []
            for m in raw_history[-6:]:
                clean_history.append({"role": m["role"], "content": m["content"]})

            messages = (
                [{"role": "system", "content": persona}]
                + clean_history
                + [{"role": "user", "content": user_msg}]
            )

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()

            try:
                stream = retry_with_backoff(
                    lambda: client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        stream=True,
                    )
                )

                reply = ""
                for chunk in stream:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        reply += delta
                        payload = json.dumps({"delta": delta})
                        self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                        self.wfile.flush()

                # Tính token & chi phí
                turn_tokens = count_tokens(user_msg, model) + count_tokens(reply, model)
                cost_info = estimate_cost(user_msg, reply, model)
                turn_cost = cost_info["total_cost"]

                done_payload = json.dumps({
                    "done": True,
                    "tokens": turn_tokens,
                    "cost": turn_cost,
                })
                self.wfile.write(f"data: {done_payload}\n\n".encode("utf-8"))
                self.wfile.flush()

            except Exception as e:
                print(f"[Server Lỗi] {str(e)}")
                err_payload = json.dumps({"delta": f"\n⚠️ [Lỗi API: {str(e)}]"})
                self.wfile.write(f"data: {err_payload}\n\n".encode("utf-8"))
                self.wfile.flush()

            self.close_connection = True
        else:
            self.send_response(404)
            self.end_headers()


def run_server(port=8000):
    from http.server import ThreadingHTTPServer
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(("0.0.0.0", port), ChatServer)
    print("=" * 60)
    print(f"🚀 WEB APP ĐÃ KHỞI ĐỘNG THÀNH CÔNG TẠI: http://localhost:{port}")
    print("👉 Mở trình duyệt (Chrome/Edge) và truy cập link trên để chat.")
    print("👉 Nhấn Ctrl + C tại terminal này khi muốn dừng server.")
    print("=" * 60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng Web Server.")


if __name__ == "__main__":
    run_server()
