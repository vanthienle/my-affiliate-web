import os
import string
import random
import sqlite3
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect, session, render_template_string
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "zalo_affiliate_secret_key_pro"
CORS(app, supports_credentials=True)

ACCESSTRADE_TOKEN = "4XeA52l7Vi-YlHdi7E1JBh43qeIX0iJ6"
BASE_DOMAIN = "https://bot-shopping.onrender.com"
DB_PATH = "links.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            code TEXT PRIMARY KEY,
            original_url TEXT,
            affiliate_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# ==========================================
# 1. TRANG CHỦ (LANDING PAGE GIỚI THIỆU)
# ==========================================

@app.route('/', methods=['GET'])
def index():
    html_home = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zalo Shopping Affiliate Portal</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-slate-900 text-slate-100 font-sans min-h-screen flex flex-col justify-between">
        <!-- Header / Navigation -->
        <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
            <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-blue-500/30">
                        <i class="fa-solid fa-cart-shopping"></i>
                    </div>
                    <span class="font-bold text-lg text-white tracking-wide">Zalo Shopping Bot</span>
                </div>
                <a href="/login" class="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition shadow-lg shadow-blue-600/30 flex items-center gap-2">
                    <i class="fa-solid fa-right-to-bracket"></i> Đăng Nhập ID
                </a>
            </div>
        </header>

        <!-- Hero Section -->
        <main class="max-w-6xl mx-auto px-6 py-16 flex-1 flex flex-col items-center justify-center text-center">
            <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold mb-6">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                Hệ Thống Tự Động Hóa Affiliate Zalo Active
            </div>

            <h1 class="text-4xl md:text-6xl font-extrabold text-white mb-6 leading-tight max-w-4xl">
                Tự Động Tạo Link & Tra Cứu Hoa Hồng Mua Sắm Dễ Dàng
            </h1>
            <p class="text-slate-400 text-base md:text-lg max-w-2xl mb-10">
                Gửi link Shopee/TikTok vào nhóm Zalo để nhận ngay link rút gọn. Đăng nhập bằng Mã Theo Dõi cá nhân để kiểm tra lịch sử đơn hàng và hoa hồng trực tiếp trên Web.
            </p>

            <!-- Action Buttons -->
            <div class="flex flex-col sm:flex-row gap-4 justify-center w-full max-w-md">
                <a href="/login" class="py-4 px-8 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold transition shadow-xl shadow-blue-600/30 flex items-center justify-center gap-3 text-base">
                    <i class="fa-solid fa-key"></i> Đăng Nhập Tra Cứu Đơn Hàng
                </a>
            </div>

            <!-- Features Grid -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20 text-left w-full">
                <div class="p-6 rounded-2xl bg-slate-800/50 border border-slate-700/60 hover:border-slate-600 transition">
                    <div class="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center text-xl mb-4">
                        <i class="fa-solid fa-bolt"></i>
                    </div>
                    <h3 class="text-lg font-bold text-white mb-2">Chuyển Link Siêu Tốc</h3>
                    <p class="text-slate-400 text-sm">Bot tự động bắt link Shopee, TikTok, Lazada trên Zalo và chuyển sang link Affiliate trong giây lát.</p>
                </div>

                <div class="p-6 rounded-2xl bg-slate-800/50 border border-slate-700/60 hover:border-slate-600 transition">
                    <div class="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center text-xl mb-4">
                        <i class="fa-solid fa-chart-line"></i>
                    </div>
                    <h3 class="text-lg font-bold text-white mb-2">Dự Báo Hoa Hồng</h3>
                    <p class="text-slate-400 text-sm">Hiển thị tỷ lệ hoa hồng % chính xác theo từng ngành hàng ngay khi bạn gửi sản phẩm vào nhóm.</p>
                </div>

                <div class="p-6 rounded-2xl bg-slate-800/50 border border-slate-700/60 hover:border-slate-600 transition">
                    <div class="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center text-xl mb-4">
                        <i class="fa-solid fa-shield-halved"></i>
                    </div>
                    <h3 class="text-lg font-bold text-white mb-2">Mã Theo Dõi Riêng Bịêt</h3>
                    <p class="text-slate-400 text-sm">Mỗi thành viên có Mã ID riêng do Bot cấp (`\id`) để bảo mật thông tin và xem đơn hàng cá nhân.</p>
                </div>
            </div>
        </main>

        <!-- Footer -->
        <footer class="border-t border-slate-800 bg-slate-900 py-6 text-center text-xs text-slate-500">
            © 2026 Zalo Affiliate Portal. All rights reserved.
        </footer>
    </body>
    </html>
    """
    return render_template_string(html_home)

# ==========================================
# 2. TRANG ĐĂNG NHẬP BẰNG ID (/login)
# ==========================================

@app.route('/login', methods=['GET'])
def login_page():
    html_login = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Đăng Nhập Mã Theo Dõi - Zalo Affiliate</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-slate-900 text-white min-h-screen flex flex-col items-center justify-center p-4">
        <div class="max-w-md w-full bg-slate-800 rounded-2xl shadow-2xl p-8 border border-slate-700">
            <a href="/" class="text-xs text-slate-400 hover:text-white flex items-center gap-1 mb-6 transition">
                <i class="fa-solid fa-arrow-left"></i> Quay lại trang chủ
            </a>

            <div class="flex items-center gap-3 mb-2">
                <div class="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold text-xl">
                    <i class="fa-solid fa-key"></i>
                </div>
                <h2 class="text-xl font-bold">Đăng Nhập Tra Cứu</h2>
            </div>
            
            <p class="text-slate-400 text-sm mb-6">Nhập Mã theo dõi do Bot Zalo cấp (Ví dụ: <code class="text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">zalo_vandotcf</code>) để kiểm tra đơn hàng.</p>

            <form id="loginForm" class="space-y-4">
                <div>
                    <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Mã Theo Dõi Cá Nhân</label>
                    <input type="text" id="trackingCode" placeholder="zalo_..." required 
                           class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition">
                </div>
                
                <div id="errMsg" class="hidden text-red-400 text-xs bg-red-500/10 p-3 rounded-xl border border-red-500/20"></div>

                <button type="submit" class="w-full py-3.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium transition shadow-lg shadow-blue-600/30 flex items-center justify-center gap-2">
                    <i class="fa-solid fa-magnifying-glass"></i> Xem Đơn Hàng & Hoa Hồng
                </button>
            </form>

            <div class="mt-6 pt-6 border-t border-slate-700/50 text-center text-xs text-slate-400">
                Chưa có mã? Vào nhóm Zalo gõ <code class="text-emerald-400 font-bold">\id</code> để nhận mã cá nhân.
            </div>
        </div>

        <script>
            document.getElementById('loginForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const code = document.getElementById('trackingCode').value.trim();
                const errMsg = document.getElementById('errMsg');
                errMsg.classList.add('hidden');

                const res = await fetch('/api/login-tracking', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ tracking_code: code })
                });
                const data = await res.json();
                if (data.success) {
                    window.location.href = '/app/orders?code=' + encodeURIComponent(code);
                } else {
                    errMsg.innerText = data.message || "Mã không hợp lệ";
                    errMsg.classList.remove('hidden');
                }
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_login)

# ==========================================
# 3. TRANG DANH SÁCH ĐƠN HÀNG (/app/orders)
# ==========================================

@app.route('/app/orders', methods=['GET'])
def orders_page():
    html_orders = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Danh Sách Đơn Hàng - Zalo Affiliate</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-slate-900 text-white min-h-screen p-4 md:p-8">
        <div class="max-w-4xl mx-auto">
            <div class="flex items-center justify-between mb-8 bg-slate-800 p-6 rounded-2xl border border-slate-700">
                <div>
                    <h1 class="text-2xl font-bold">📋 Báo Cáo Đơn Hàng & Hoa Hồng</h1>
                    <p class="text-slate-400 text-sm mt-1">Mã theo dõi: <span id="userCode" class="text-blue-400 font-mono font-bold bg-blue-500/10 px-2 py-0.5 rounded"></span></p>
                </div>
                <div class="flex gap-2">
                    <a href="/" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs rounded-xl transition flex items-center gap-1">
                        <i class="fa-solid fa-house"></i> Trang chủ
                    </a>
                    <a href="/login" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs rounded-xl transition flex items-center gap-1">
                        <i class="fa-solid fa-arrow-right-from-bracket"></i> Đổi Mã
                    </a>
                </div>
            </div>

            <div class="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden shadow-xl">
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm text-slate-300">
                        <thead class="bg-slate-900/50 text-xs uppercase text-slate-400 border-b border-slate-700">
                            <tr>
                                <th class="p-4">Mã Đơn</th>
                                <th class="p-4">Sản Phẩm</th>
                                <th class="p-4">Giá Trị</th>
                                <th class="p-4">Hoa Hồng</th>
                                <th class="p-4">Trạng Thái</th>
                            </tr>
                        </thead>
                        <tbody id="ordersTable" class="divide-y divide-slate-700/50">
                            <tr><td colspan="5" class="p-8 text-center text-slate-500">Đang tải dữ liệu đơn hàng...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <script>
            const urlParams = new URLSearchParams(window.location.search);
            const code = urlParams.get('code');
            document.getElementById('userCode').innerText = code || "N/A";

            async function loadOrders() {
                const res = await fetch('/api/user-orders?tracking_code=' + encodeURIComponent(code));
                const data = await res.json();
                const tbody = document.getElementById('ordersTable');
                
                if (data.success && data.orders.length > 0) {
                    tbody.innerHTML = data.orders.map(o => `
                        <tr class="hover:bg-slate-700/30 transition">
                            <td class="p-4 font-mono text-xs text-slate-400">${o.order_id}</td>
                            <td class="p-4 font-medium text-white">${o.product_name}</td>
                            <td class="p-4">${Number(o.price).toLocaleString()}đ</td>
                            <td class="p-4 text-emerald-400 font-bold">+${Number(o.commission).toLocaleString()}đ</td>
                            <td class="p-4">
                                <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${o.status === 'Thành công' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'}">
                                    ${o.status}
                                </span>
                            </td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = `<tr><td colspan="5" class="p-8 text-center text-slate-500">Chưa có đơn hàng nào phát sinh cho ID này trong 30 ngày qua.</td></tr>`;
                }
            }
            if (code) loadOrders();
        </script>
    </body>
    </html>
    """
    return render_template_string(html_orders)

# ==========================================
# 4. CÁC API BACKEND DÙNG CHO BOT & WEB
# ==========================================

@app.route('/api/convert', methods=['POST'])
def convert_url():
    data = request.json or {}
    raw_url = data.get('url', '').strip()
    if not raw_url:
        return jsonify({"success": False, "message": "URL không hợp lệ"}), 400

    code = generate_short_code()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO links (code, original_url, affiliate_url) VALUES (?, ?, ?)',
                   (code, raw_url, raw_url))
    conn.commit()
    conn.close()

    short_link = f"{BASE_DOMAIN}/s/{code}"
    return jsonify({"success": True, "data": {"short_link": short_link, "code": code}})

@app.route('/s/<code>', methods=['GET'])
def redirect_short_link(code):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT original_url, affiliate_url FROM links WHERE code = ?', (code,))
    row = cursor.fetchone()
    conn.close()

    if row:
        target_url = row[1] if row[1] else row[0]
        return redirect(target_url, code=302)
    return "Link không tồn tại hoặc đã hết hạn", 404

@app.route('/api/login-tracking', methods=['POST'])
def login_tracking():
    data = request.json or {}
    tracking_code = data.get('tracking_code', '').strip().lower()

    if not tracking_code:
        return jsonify({"success": False, "message": "Vui lòng nhập Mã theo dõi"}), 400

    session['user_utm'] = tracking_code
    return jsonify({
        "success": True,
        "message": "Đăng nhập thành công",
        "tracking_code": tracking_code,
        "redirect": f"/app/orders?code={tracking_code}"
    })

@app.route('/api/user-orders', methods=['GET'])
def get_user_orders():
    tracking_code = request.args.get('tracking_code') or session.get('user_utm')
    if not tracking_code:
        return jsonify({"success": False, "message": "Chưa cung cấp Mã theo dõi"}), 401

    tracking_code = tracking_code.strip().lower()
    today = datetime.now()
    start_day = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")

    api_url = f"https://api.accesstrade.vn/v1/transactions?since={start_day}&until={today_str}"
    headers = {"Authorization": f"Token {ACCESSTRADE_TOKEN}"}

    try:
        resp = requests.get(api_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            all_orders = resp.json().get("data", [])
            user_orders = []
            for o in all_orders:
                utm = str(o.get("utm_source", "")).lower()
                if tracking_code in utm:
                    st = str(o.get("status", o.get("order_status", "")))
                    status_text = "Thành công" if st == "1" else ("Chờ duyệt" if st == "0" else "Đã hủy")
                    pub_comm = float(o.get("pub_commission", 0) or 0) * 0.8
                    user_orders.append({
                        "order_id": o.get("order_id", ""),
                        "product_name": o.get("product_name", "Sản phẩm TMĐT"),
                        "price": float(o.get("sales_price", 0) or 0),
                        "commission": pub_comm,
                        "status": status_text,
                        "created_at": o.get("click_time", o.get("created_at", ""))
                    })
            return jsonify({"success": True, "tracking_code": tracking_code, "orders": user_orders})
        return jsonify({"success": False, "message": f"Lỗi AccessTrade HTTP {resp.status_code}"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
