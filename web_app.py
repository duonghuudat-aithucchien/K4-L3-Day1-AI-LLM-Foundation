"""
Web App Tổng Hợp Cả 4 Part - K4 LLM Foundation
Tích hợp đầy đủ demo trực quan cho từng phần:
    - Tab 1: 💬 Trợ Lý Hội Thoại Hoàn Chỉnh (Part 4)
    - Tab 2: ⚖️ So Sánh Song Song GPT-4o vs Mini (Part 1)
    - Tab 3: 🧮 Máy Đếm Token & Tính Chi Phí (Part 2)
    - Tab 4: 🛡️ Mô Phỏng Streaming & Retry Backoff (Part 3)

Khởi động:
    python web_app.py
Truy cập:
    http://localhost:8000
"""

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from dotenv import load_dotenv

load_dotenv()

# Import đầy đủ các hàm cốt lõi từ template.py
from template import (
    OPENAI_MODEL,
    OPENAI_MINI_MODEL,
    PRICING_PER_1K_TOKENS,
    call_openai,
    call_openai_mini,
    compare_models,
    count_tokens,
    estimate_cost,
    retry_with_backoff,
)

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="vi" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Lab 01 Hub - K4 LLM Foundation</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>

    <style>
        :root {
            --bg-body: #090d16;
            --bg-sidebar: #0f172a;
            --bg-surface: #1e293b;
            --bg-input: #141e33;
            --border: rgba(255, 255, 255, 0.08);
            --primary: #38bdf8;
            --primary-glow: rgba(56, 189, 248, 0.18);
            --accent: #818cf8;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --user-bubble-bg: linear-gradient(135deg, #0284c7, #2563eb);
            --assistant-bubble: #172033;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg-body);
            color: var(--text-main);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        /* SIDEBAR */
        aside {
            width: 320px;
            background-color: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 20px;
            gap: 16px;
            z-index: 10;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            padding-bottom: 14px;
            border-bottom: 1px solid var(--border);
        }
        .brand-logo {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: linear-gradient(135deg, #38bdf8, #6366f1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            box-shadow: 0 0 16px var(--primary-glow);
        }
        .brand-text h1 { font-size: 1rem; font-weight: 700; color: #f8fafc; }
        .brand-text span { font-size: 0.7rem; color: #38bdf8; font-weight: 600; text-transform: uppercase; }

        /* NAVIGATION TABS */
        .nav-menu {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .nav-btn {
            display: flex;
            align-items: center;
            gap: 10px;
            background: transparent;
            border: 1px solid transparent;
            color: var(--text-muted);
            padding: 10px 14px;
            border-radius: 10px;
            font-size: 0.86rem;
            font-weight: 600;
            cursor: pointer;
            text-align: left;
            transition: all 0.2s;
        }
        .nav-btn:hover {
            background: rgba(255, 255, 255, 0.04);
            color: #f1f5f9;
        }
        .nav-btn.active {
            background: rgba(56, 189, 248, 0.12);
            color: #38bdf8;
            border-color: rgba(56, 189, 248, 0.35);
        }

        /* DYNAMIC CONTROLS */
        .tab-settings {
            display: flex;
            flex-direction: column;
            gap: 14px;
            flex: 1;
            overflow-y: auto;
        }
        .form-group { display: flex; flex-direction: column; gap: 6px; }
        label { font-size: 0.78rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; }

        select, textarea, input[type="text"] {
            background-color: var(--bg-input);
            border: 1px solid var(--border);
            color: var(--text-main);
            border-radius: 8px;
            padding: 9px 12px;
            font-size: 0.85rem;
            outline: none;
            font-family: inherit;
        }
        select:focus, textarea:focus, input:focus { border-color: var(--primary); }

        .stats-card {
            margin-top: auto;
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .stat-item {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: var(--text-muted);
        }
        .stat-val { font-family: 'JetBrains Mono', monospace; font-weight: 600; color: #f1f5f9; }
        .stat-val.green { color: #34d399; }

        /* MAIN CONTENT VIEWS */
        main {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: radial-gradient(circle at 50% 0%, #151e33 0%, var(--bg-body) 65%);
            position: relative;
            overflow: hidden;
        }

        header {
            padding: 16px 28px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(8px);
        }
        .header-title { font-size: 0.95rem; font-weight: 700; display: flex; align-items: center; gap: 8px; }

        .view-content {
            flex: 1;
            display: none;
            height: calc(100vh - 65px);
            overflow-y: auto;
        }
        .view-content.active { display: flex; flex-direction: column; }

        /* TAB 1: CHATBOT STYLES */
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 24px 30px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .msg-row { display: flex; gap: 12px; max-width: 82%; animation: fadeIn 0.2s ease forwards; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
        .msg-row.user { align-self: flex-end; flex-direction: row-reverse; }
        .msg-row.assistant { align-self: flex-start; }
        .avatar { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0; }
        .msg-row.user .avatar { background: #2563eb; color: white; }
        .msg-row.assistant .avatar { background: linear-gradient(135deg, #0ea5e9, #6366f1); color: white; }
        .msg-bubble { padding: 12px 16px; border-radius: 14px; font-size: 0.92rem; line-height: 1.6; }
        .msg-row.user .msg-bubble { background: var(--user-bubble-bg); color: white; border-bottom-right-radius: 2px; }
        .msg-row.assistant .msg-bubble { background: var(--assistant-bubble); color: #f1f5f9; border: 1px solid var(--border); border-bottom-left-radius: 2px; }
        .input-wrapper { padding: 18px 28px; background: rgba(15, 23, 42, 0.8); border-top: 1px solid var(--border); }
        .input-bar { background: var(--bg-input); border: 1px solid var(--border); border-radius: 16px; padding: 6px 10px 6px 18px; display: flex; align-items: center; gap: 10px; }
        .input-bar input { flex: 1; background: transparent; border: none; color: white; font-size: 0.92rem; outline: none; }
        .btn-send { width: 38px; height: 38px; border-radius: 10px; background: var(--primary); border: none; color: #090d16; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; }

        /* TAB 2: COMPARE MODELS (PART 1) */
        .compare-view {
            padding: 30px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            max-width: 1100px;
            margin: 0 auto;
            width: 100%;
        }
        .action-bar { display: flex; gap: 12px; }
        .action-bar input { flex: 1; font-size: 0.95rem; }
        .btn-action {
            background: linear-gradient(135deg, #38bdf8, #2563eb);
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            white-space: nowrap;
        }
        .btn-action:disabled { opacity: 0.5; cursor: not-allowed; }
        .compare-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            flex: 1;
        }
        .compare-col {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }
        .col-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 10px; }
        .badge-model { padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; font-family: 'JetBrains Mono'; }
        .badge-4o { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
        .badge-mini { background: rgba(52, 211, 153, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }
        .metric-tag { font-size: 0.8rem; font-family: 'JetBrains Mono'; color: var(--text-muted); }
        .result-box { flex: 1; background: #0f172a; border-radius: 10px; padding: 14px; font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap; overflow-y: auto; }

        /* TAB 3: TOKEN CALCULATOR (PART 2) */
        .token-view {
            padding: 30px;
            display: flex;
            flex-direction: column;
            gap: 24px;
            max-width: 900px;
            margin: 0 auto;
            width: 100%;
        }
        .metrics-cards {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        }
        .metric-card {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .metric-title { font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 600; }
        .metric-value { font-family: 'JetBrains Mono'; font-size: 1.3rem; font-weight: 700; color: #f1f5f9; }

        /* TAB 4: RETRY & RESILIENCE (PART 3) */
        .resilience-view {
            padding: 30px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            max-width: 900px;
            margin: 0 auto;
            width: 100%;
        }
        .timeline {
            display: flex;
            flex-direction: column;
            gap: 12px;
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
        }
        .timeline-step {
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 12px;
            border-radius: 8px;
            background: #0f172a;
            font-family: 'JetBrains Mono';
            font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <!-- SIDEBAR -->
    <aside>
        <div class="brand">
            <div class="brand-logo">⚡</div>
            <div class="brand-text">
                <h1>AI Lab Hub</h1>
                <span>K4 LLM Foundation</span>
            </div>
        </div>

        <!-- NAVIGATION TABS -->
        <div class="nav-menu">
            <button class="nav-btn active" onclick="switchTab('tab-chat')">💬 Part 4 — Trợ Lý CLI Chatbot</button>
            <button class="nav-btn" onclick="switchTab('tab-compare')">⚖️ Part 1 — So Sánh 2 Model</button>
            <button class="nav-btn" onclick="switchTab('tab-token')">🧮 Part 2 — Token & Chi Phí</button>
            <button class="nav-btn" onclick="switchTab('tab-retry')">🛡️ Part 3 — Streaming & Retry</button>
        </div>

        <!-- SETTINGS PANEL CHO CHATBOT -->
        <div class="tab-settings" id="chatSettings">
            <div class="form-group">
                <label>Model Chatbot</label>
                <select id="chatModel">
                    <option value="gpt-4o">GPT-4o (Chính)</option>
                    <option value="gpt-4o-mini">GPT-4o-mini (Rẻ & Nhanh)</option>
                </select>
            </div>
            <div class="form-group">
                <label>Persona (System Prompt)</label>
                <textarea id="chatPersona" rows="4">Bạn là trợ giảng lập trình AI thân thiện và kiên nhẫn. Luôn trả lời ngắn gọn (dưới 150 từ), giải thích bằng tiếng Việt tự nhiên và cung cấp ví dụ code minh họa tối giản khi giải thích khái niệm.</textarea>
            </div>
            <div class="form-group">
                <label>Temperature: <span id="tempVal" style="color:#38bdf8;">0.7</span></label>
                <input type="range" id="chatTemp" min="0.0" max="1.5" step="0.1" value="0.7" oninput="document.getElementById('tempVal').innerText = this.value">
            </div>
        </div>

        <div class="stats-card">
            <div class="stat-item"><span>Lượt chat:</span><span class="stat-val" id="statTurns">0</span></div>
            <div class="stat-item"><span>Tokens:</span><span class="stat-val" id="statTokens">0</span></div>
            <div class="stat-item"><span>Tổng chi phí:</span><span class="stat-val green" id="statCost">$0.0000</span></div>
            <div class="stat-item"><span>Quy đổi:</span><span class="stat-val green" id="statVnd">~0 đ</span></div>
        </div>
    </aside>

    <!-- MAIN VIEWS -->
    <main>
        <header>
            <div class="header-title" id="headerTitle">💬 Trợ Lý CLI Chatbot (Part 4)</div>
            <div style="font-size:0.75rem; color:#10b981; font-weight:600;">● Online</div>
        </header>

        <!-- VIEW 1: CHATBOT (PART 4) -->
        <div class="view-content active" id="tab-chat">
            <div class="chat-container" id="chatBox">
                <div class="msg-row assistant">
                    <div class="avatar">🤖</div>
                    <div class="msg-bubble">Chào bạn! Mình là trợ lý AI được xây dựng theo đúng bài Lab Day 1. Hãy thử nhập câu hỏi hoặc chọn các tab bên trái để trải nghiệm Part 1, 2, 3 nhé!</div>
                </div>
            </div>
            <div class="input-wrapper">
                <div class="input-bar">
                    <input type="text" id="userInput" placeholder="Nhập tin nhắn..." onkeydown="if(event.key==='Enter') sendChatMessage()">
                    <button class="btn-send" onclick="sendChatMessage()">➤</button>
                </div>
            </div>
        </div>

        <!-- VIEW 2: COMPARE MODELS (PART 1) -->
        <div class="view-content" id="tab-compare">
            <div class="compare-view">
                <div>
                    <h2 style="font-size:1.2rem; margin-bottom:6px;">⚖️ So Sánh Trực Tiếp GPT-4o vs GPT-4o-mini</h2>
                    <p style="font-size:0.85rem; color:var(--text-muted);">Gửi cùng 1 prompt lên cả hai mô hình để đo lường sự đánh đổi giữa độ trễ, chất lượng và chi phí.</p>
                </div>
                <div class="action-bar">
                    <input type="text" id="comparePrompt" value="Giải thích khác biệt giữa temperature và top_p trong một câu.">
                    <button class="btn-action" id="btnCompare" onclick="runCompare()">🚀 Chạy So Sánh</button>
                </div>
                <div class="compare-grid">
                    <div class="compare-col">
                        <div class="col-header">
                            <span class="badge-model badge-4o">GPT-4o (Model lớn)</span>
                            <span class="metric-tag" id="gpt4oLatency">Độ trễ: -- s</span>
                        </div>
                        <div class="result-box" id="gpt4oResponse">Bấm nút "Chạy So Sánh" để bắt đầu...</div>
                    </div>
                    <div class="compare-col">
                        <div class="col-header">
                            <span class="badge-model badge-mini">GPT-4o-mini (Model nhỏ)</span>
                            <span class="metric-tag" id="miniLatency">Độ trễ: -- s</span>
                        </div>
                        <div class="result-box" id="miniResponse">Bấm nút "Chạy So Sánh" để bắt đầu...</div>
                    </div>
                </div>
                <div style="background:var(--bg-surface); padding:14px; border-radius:10px; font-size:0.85rem; border:1px solid var(--border);" id="compareCostInfo">
                    💡 <b>Chi phí ước tính:</b> GPT-4o đắt hơn GPT-4o-mini khoảng 16.7 lần cho cùng số token đầu ra.
                </div>
            </div>
        </div>

        <!-- VIEW 3: TOKEN CALCULATOR (PART 2) -->
        <div class="view-content" id="tab-token">
            <div class="token-view">
                <div>
                    <h2 style="font-size:1.2rem; margin-bottom:6px;">🧮 Đo Lường Token & Phân Tích Chi Phí</h2>
                    <p style="font-size:0.85rem; color:var(--text-muted);">Thử nghiệm tại sao tiếng Việt lại tốn nhiều token hơn tiếng Anh cùng độ dài theo bộ mã hóa tiktoken.</p>
                </div>
                <div class="form-group">
                    <label>Nhập đoạn văn bản cần đếm</label>
                    <textarea id="tokenText" rows="5" oninput="analyzeTokens()">Việt Nam là quốc gia xuất khẩu cà phê Robusta lớn nhất thế giới. Mô hình ngôn ngữ lớn xử lý văn bản tiếng Việt thông qua các token subword.</textarea>
                </div>
                <div class="metrics-cards">
                    <div class="metric-card">
                        <span class="metric-title">Số Từ (Words)</span>
                        <span class="metric-value" id="valWords">0</span>
                    </div>
                    <div class="metric-card">
                        <span class="metric-title">Ước Lượng (Từ / 0.75)</span>
                        <span class="metric-value" id="valEstimate">0</span>
                    </div>
                    <div class="metric-card">
                        <span class="metric-title">Token Thật (tiktoken)</span>
                        <span class="metric-value" style="color:#38bdf8;" id="valRealTokens">0</span>
                    </div>
                    <div class="metric-card">
                        <span class="metric-title">Chênh Lệch Tiếng Việt</span>
                        <span class="metric-value" style="color:#f59e0b;" id="valDiff">+0%</span>
                    </div>
                </div>
                <div style="background:var(--bg-surface); padding:16px; border-radius:12px; font-size:0.88rem; line-height:1.6; border:1px solid var(--border);">
                    📌 <b>Giải thích bản chất (Part 2):</b> Tokenizer của OpenAI (Byte-Pair Encoding) được huấn luyện chủ yếu trên tiếng Anh. Các từ tiếng Việt có dấu thanh và ký tự Unicode đa byte thường bị phân tách thành 2 đến 3 token nhỏ, khiến chi phí thực tế cao hơn công thức đếm từ khoảng 15% – 35%.
                </div>
            </div>
        </div>

        <!-- VIEW 4: RETRY & STREAMING (PART 3) -->
        <div class="view-content" id="tab-retry">
            <div class="resilience-view">
                <div>
                    <h2 style="font-size:1.2rem; margin-bottom:6px;">🛡️ Trực Quan Hóa Exponential Backoff & Streaming</h2>
                    <p style="font-size:0.85rem; color:var(--text-muted);">Mô phỏng cơ chế tự động thử lại an toàn khi API server gặp lỗi nghẽn mạng hoặc Rate Limit (429).</p>
                </div>
                <button class="btn-action" onclick="simulateRetry()" style="align-self:flex-start;">▶️ Chạy Mô Phỏng Thử Lại (Retry Simulation)</button>
                <div class="timeline" id="retryTimeline">
                    <div class="timeline-step">⚡ Bấm nút phía trên để xem các bước thử lại với thời gian chờ tăng gấp đôi...</div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let history = [];
        let totalTokens = 0;
        let totalCost = 0.0;
        let numTurns = 0;

        function switchTab(tabId) {
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.view-content').forEach(v => v.classList.remove('active'));

            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');

            const titles = {
                'tab-chat': '💬 Trợ Lý CLI Chatbot (Part 4)',
                'tab-compare': '⚖️ So Sánh 2 Model Song Song (Part 1)',
                'tab-token': '🧮 Đo Lường Token & Chi Phí (Part 2)',
                'tab-retry': '🛡️ Streaming & Exponential Backoff (Part 3)'
            };
            document.getElementById('headerTitle').innerText = titles[tabId];

            if (tabId === 'tab-token') analyzeTokens();
        }

        /* --- PART 4: CHATBOT --- */
        async function sendChatMessage() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();
            if (!text) return;

            const chatBox = document.getElementById('chatBox');
            const model = document.getElementById('chatModel').value;
            const persona = document.getElementById('chatPersona').value;
            const temperature = parseFloat(document.getElementById('chatTemp').value);

            chatBox.innerHTML += `
                <div class="msg-row user">
                    <div class="avatar">👤</div>
                    <div class="msg-bubble">${text}</div>
                </div>
                <div class="msg-row assistant">
                    <div class="avatar">🤖</div>
                    <div class="msg-bubble" id="liveStream">...</div>
                </div>
            `;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            const assistBubble = document.getElementById('liveStream');

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ message: text, history: history, model: model, persona: persona, temperature: temperature })
                });

                const reader = res.body.getReader();
                const decoder = new TextDecoder('utf-8');
                let full = '', buffer = '', isDone = false;
                assistBubble.innerText = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop();

                    for (const l of lines) {
                        const t = l.trim();
                        if (t.startsWith('data: ')) {
                            const d = JSON.parse(t.slice(6));
                            if (d.delta) {
                                full += d.delta;
                                assistBubble.innerHTML = marked.parse(full);
                                chatBox.scrollTop = chatBox.scrollHeight;
                            }
                            if (d.done) {
                                history.push({role: 'user', content: text});
                                history.push({role: 'assistant', content: full});
                                if (history.length > 6) history = history.slice(-6);
                                numTurns += 1;
                                totalTokens += d.tokens;
                                totalCost += d.cost;
                                document.getElementById('statTurns').innerText = numTurns;
                                document.getElementById('statTokens').innerText = totalTokens;
                                document.getElementById('statCost').innerText = '$' + totalCost.toFixed(5);
                                document.getElementById('statVnd').innerText = '~' + Math.round(totalCost * 25500) + ' đ';
                                isDone = true;
                                break;
                            }
                        }
                    }
                    if (isDone) { await reader.cancel(); break; }
                }
            } catch (e) {
                assistBubble.innerText = 'Lỗi: ' + e.message;
            } finally {
                assistBubble.removeAttribute('id');
            }
        }

        /* --- PART 1: COMPARE --- */
        async function runCompare() {
            const prompt = document.getElementById('comparePrompt').value.trim();
            if (!prompt) return;

            const btn = document.getElementById('btnCompare');
            btn.disabled = true;
            btn.innerText = 'Đang gọi 2 API...';

            document.getElementById('gpt4oResponse').innerText = 'Đang xử lý GPT-4o...';
            document.getElementById('miniResponse').innerText = 'Đang xử lý GPT-4o-mini...';

            try {
                const res = await fetch('/api/compare', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ prompt: prompt })
                });
                const data = await res.json();
                document.getElementById('gpt4oResponse').innerText = data.gpt4o_response;
                document.getElementById('miniResponse').innerText = data.mini_response;
                document.getElementById('gpt4oLatency').innerText = `Độ trễ: ${data.gpt4o_latency.toFixed(2)}s`;
                document.getElementById('miniLatency').innerText = `Độ trễ: ${data.mini_latency.toFixed(2)}s`;
                document.getElementById('compareCostInfo').innerHTML = `
                    💰 <b>Chi phí output ước tính:</b> GPT-4o: <code>$${data.gpt4o_cost_estimate.toFixed(6)}</code> | Mini: rẻ hơn ~16.7 lần (~<code>$${(data.gpt4o_cost_estimate / 16.67).toFixed(6)}</code>).
                `;
            } catch (e) {
                alert('Lỗi so sánh: ' + e.message);
            } finally {
                btn.disabled = false;
                btn.innerText = '🚀 Chạy So Sánh';
            }
        }

        /* --- PART 2: TOKEN ANALYZER --- */
        async function analyzeTokens() {
            const text = document.getElementById('tokenText').value;
            const words = text.trim() ? text.trim().split(/\s+/).length : 0;
            const est = Math.round(words / 0.75);

            document.getElementById('valWords').innerText = words;
            document.getElementById('valEstimate').innerText = est;

            try {
                const res = await fetch('/api/tokens', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ text: text })
                });
                const data = await res.json();
                document.getElementById('valRealTokens').innerText = data.tokens;
                const diff = est > 0 ? Math.round(((data.tokens - est) / est) * 100) : 0;
                document.getElementById('valDiff').innerText = (diff >= 0 ? '+' : '') + diff + '%';
            } catch (e) {
                console.error(e);
            }
        }

        /* --- PART 3: RETRY SIMULATION --- */
        async function simulateRetry() {
            const timeline = document.getElementById('retryTimeline');
            timeline.innerHTML = '<div class="timeline-step">🔄 Bắt đầu gọi API lần đầu...</div>';
            
            await new Promise(r => setTimeout(r, 600));
            timeline.innerHTML += '<div class="timeline-step" style="color:#f87171;">❌ Lần 1: Gặp lỗi HTTP 429 (Rate limit / Server Busy)</div>';
            timeline.innerHTML += '<div class="timeline-step" style="color:#38bdf8;">⏳ Chờ Base Delay: 0.1s (Exponential Backoff: 0.1 × 2⁰)...</div>';

            await new Promise(r => setTimeout(r, 800));
            timeline.innerHTML += '<div class="timeline-step" style="color:#f87171;">❌ Lần 2: Thử lại lần 1 vẫn lỗi HTTP 429</div>';
            timeline.innerHTML += '<div class="timeline-step" style="color:#38bdf8;">⏳ Chờ tăng gấp đôi: 0.2s (Exponential Backoff: 0.1 × 2¹)...</div>';

            await new Promise(r => setTimeout(r, 1000));
            timeline.innerHTML += '<div class="timeline-step" style="color:#f87171;">❌ Lần 3: Thử lại lần 2 vẫn quá tải</div>';
            timeline.innerHTML += '<div class="timeline-step" style="color:#38bdf8;">⏳ Chờ tăng gấp đôi: 0.4s (Exponential Backoff: 0.1 × 2²)...</div>';

            await new Promise(r => setTimeout(r, 1200));
            timeline.innerHTML += '<div class="timeline-step" style="color:#34d399; font-weight:700;">✅ Lần 4: Server đã giải tỏa nghẽn - Lời gọi API THÀNH CÔNG! Bắt đầu Stream response...</div>';
        }
    </script>
</body>
</html>
"""


class ChatServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

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
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        req = json.loads(body.decode("utf-8")) if body else {}

        # 1. API COMPARE (PART 1)
        if self.path == "/api/compare":
            prompt = req.get("prompt", "Hello")
            res = compare_models(prompt)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))
            self.close_connection = True

        # 2. API TOKEN CALCULATOR (PART 2)
        elif self.path == "/api/tokens":
            text = req.get("text", "")
            tokens = count_tokens(text)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(json.dumps({"tokens": tokens}).encode("utf-8"))
            self.close_connection = True

        # 3. API CHATBOT (PART 4 + PART 3 STREAMING)
        elif self.path == "/api/chat":
            user_msg = req.get("message", "")
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
                err_payload = json.dumps({"delta": f"\n⚠️ [Lỗi API: {str(e)}]"})
                self.wfile.write(f"data: {err_payload}\n\n".encode("utf-8"))
                self.wfile.flush()

            self.close_connection = True
        else:
            self.send_response(404)
            self.end_headers()


def run_server(port=8000):
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(("0.0.0.0", port), ChatServer)
    print("=" * 70)
    print(f"🚀 TẤT CẢ 4 PART ĐÃ SẴN SÀNG TRÊN WEB: http://localhost:{port}")
    print("  - Tab 1: 💬 Trợ lý Chatbot CLI (Part 4)")
    print("  - Tab 2: ⚖️ So sánh 2 Model Song Song (Part 1)")
    print("  - Tab 3: 🧮 Máy đếm Token & Chi phí (Part 2)")
    print("  - Tab 4: 🛡️ Trực quan hóa Streaming & Retry Backoff (Part 3)")
    print("=" * 70)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng server.")


if __name__ == "__main__":
    run_server()
