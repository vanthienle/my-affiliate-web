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
# 1. TRANG CHỦ (CONVERT LINK NAY TRÊN WEB)
# ==========================================

@app.route('/', methods=['GET'])
def index():
    html_home = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chuyển Đổi Link Mua Sắm - Nhận Hoa Hồng</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-[#FAF8F5] text-slate-800 font-sans min-h-screen flex flex-col justify-between relative overflow-x-hidden">
        
        <!-- Hình trang trí phông nền -->
        <div class="absolute -top-20 -left-20 w-80 h-80 bg-red-100/50 rounded-full blur-3xl -z-10"></div>
        <div class="absolute top-1/3 -right-20 w-96 h-96 bg-orange-100/40 rounded-full blur-3xl -z-10"></div>

        <!-- HEADER / NAVIGATION -->
        <header class="max-w-6xl w-full mx-auto px-4 py-6 flex items-center justify-between">
            <div class="flex items-center gap-2">
                <div class="w-10 h-10 bg-red-500 rounded-xl flex items-center justify-center text-white shadow-md shadow-red-500/20">
                    <i class="fa-solid fa-gift text-xl"></i>
                </div>
            </div>

            <nav class="hidden md:flex items-center gap-1 bg-white/80 backdrop-blur border border-slate-200/80 rounded-full px-3 py-1.5 shadow-sm">
                <a href="/" class="px-4 py-2 rounded-full bg-red-50 text-red-600 font-medium text-sm flex items-center gap-2">
                    <i class="fa-solid fa-house text-xs"></i> Trang chủ
                </a>
                <a href="/login" class="px-4 py-2 rounded-full hover:bg-slate-100 text-slate-600 font-medium text-sm transition flex items-center gap-2">
                    <i class="fa-solid fa-magnifying-glass text-xs"></i> Tra cứu đơn hàng
                </a>
                <a href="/login" class="px-4 py-2 rounded-full hover:bg-slate-100 text-slate-600 font-medium text-sm transition flex items-center gap-2">
                    <i class="fa-solid fa-wallet text-xs"></i> Ví của bạn
                </a>
                <a href="#guide" class="px-4 py-2 rounded-full hover:bg-slate-100 text-slate-600 font-medium text-sm transition flex items-center gap-2">
                    <i class="fa-solid fa-circle-question text-xs"></i> Hướng dẫn
                </a>
            </nav>

            <a href="/login" class="px-5 py-2.5 rounded-full bg-white border border-red-200 hover:bg-red-50 text-red-600 font-medium text-sm shadow-sm transition flex items-center gap-2">
                <i class="fa-solid fa-right-to-bracket text-xs"></i> Đăng nhập ID
            </a>
        </header>

        <!-- MAIN HERO CONTENT -->
        <main class="max-w-4xl mx-auto px-4 py-12 text-center flex-1 flex flex-col items-center justify-center">
            
            <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-red-50 border border-red-100 text-red-500 text-xs font-semibold mb-6">
                <span>✨ Nền tảng Affiliate uy tín tại Việt Nam</span>
            </div>

            <h1 class="text-4xl md:text-6xl font-black text-slate-900 mb-4 tracking-tight">
                Chuyển đổi link mua sắm<br/>
                <span class="text-[#E85B46]">Nhận hoa hồng</span>
            </h1>

            <p class="text-slate-500 text-base md:text-lg mb-10 max-w-xl">
                Hoa hồng các đơn hàng từ Shopee, Lazada, TikTok Shop — công khai, minh bạch
            </p>

            <!-- KHUNG DÁN LINK CONVERT TRỰC TIẾP -->
            <div class="w-full bg-white rounded-3xl p-4 md:p-6 shadow-xl shadow-slate-200/50 border border-slate-100 text-left">
                
                <!-- Bảng các sàn hỗ trợ -->
                <div class="flex items-center gap-6 mb-4 px-2">
                    <span class="flex items-center gap-1.5 text-xs font-semibold text-orange-600">
                        <i class="fa-solid fa-bag-shopping"></i> Shopee
                    </span>
                    <span class="flex items-center gap-1.5 text-xs font-semibold text-slate-900">
                        <i class="fa-brands fa-tiktok"></i> TikTok
                    </span>
                    <span class="flex items-center gap-1.5 text-xs font-semibold text-blue-600">
                        <i class="fa-solid fa-layer-group"></i> Lazada
                    </span>
                </div>

                <!-- Input Box Group -->
                <div class="flex flex-col md:flex-row gap-2">
                    <button type="button" id="pasteBtn" class="px-4 py-3 bg-red-50 hover:bg-red-100 text-red-600 rounded-2xl font-medium text-sm transition flex items-center justify-center gap-2">
                        <i class="fa-solid fa-paste"></i> Dán
                    </button>
                    
                    <div class="flex-1 relative">
                        <input type="text" id="rawUrl" placeholder="Dán link sản phẩm..." 
                               class="w-full bg-slate-50 border border-slate-200 focus:border-red-400 focus:bg-white rounded-2xl px-4 py-3.5 text-slate-800 placeholder-slate-400 focus:outline-none transition text-sm">
                    </div>

                    <button type="button" id="convertBtn" class="px-6 py-3.5 bg-[#E85B46] hover:bg-[#d44a36] text-white font-medium rounded-2xl transition shadow-lg shadow-red-500/20 text-sm flex items-center justify-center gap-2">
                        <i class="fa-solid fa-diagram-project"></i> Chuyển đổi link
                    </button>
                </div>

                <p class="text-xs text-slate-400 mt-3 px-2">
                    ≡ Dán nhiều link chuyển đổi cùng lúc, mỗi link 1 dòng
                </p>

                <!-- KHU VỰC HIỆN KẾT QUẢ LINK AFTER CONVERT -->
                <div id="resultBox" class="hidden mt-6 pt-6 border-t border-slate-100">
                    <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Link rút gọn của bạn:</label>
                    <div class="flex gap-2">
                        <input type="text" id="outLink" readonly class="flex-1 bg-emerald-50 border border-emerald-200 text-emerald-700 font-medium rounded-xl px-4 py-3 text-sm focus:outline-none">
                        <button type="button" id="copyBtn" class="px-5 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-xl text-sm transition">
                            <i class="fa-solid fa-copy"></i> Sao chép
                        </button>
                    </div>
                </div>
            </div>

            <!-- Nút Bắt đầu miễn phí -->
            <div class="mt-8">
                <a href="/login" class="px-8 py-3.5 bg-slate-900 hover:bg-slate-800 text-white font-medium rounded-full shadow-lg transition text-sm inline-flex items-center gap-2">
                    <i class="fa-solid fa-bolt text-yellow-400"></i> Bắt đầu miễn phí
                </a>
            </div>
        </main>

        <footer class="py-6 text-center text-xs text-slate-400 border-t border-slate-200/60">
            © 2026 Zalo Shopping Affiliate. Tất cả quyền được bảo lưu.
        </footer>

        <script>
            // Xử lý nút Dán từ Clipboard
            document.getElementById('pasteBtn').addEventListener('click', async () => {
                try {
                    const text = await navigator.clipboard.readText();
                    document.getElementById('rawUrl').value = text;
                } catch (err) {
                    alert('Hãy cấp quyền truy cập Clipboard hoặc dán thủ công!');
                }
            });

            // Xử lý Chuyển đổi Link
            document.getElementById('convertBtn').addEventListener('click', async () => {
                const url = document.getElementById('rawUrl').value.trim();
                if (!url) {
                    alert('Vui lòng dán link sản phẩm cần chuyển đổi!');
                    return;
                }

                const res = await fetch('/api/convert', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url })
                });

                const result = await res.json();
                if (result.success) {
                    document.getElementById('outLink').value = result.data.short_link;
                    document.getElementById('resultBox').classList.remove('hidden');
                } else {
                    alert('Lỗi chuyển đổi link!');
                }
            });

            // Xử lý Sao Chép
            document.getElementById('copyBtn').addEventListener('click', () => {
                const outLink = document.getElementById('outLink');
                outLink.select();
                document.execCommand('copy');
                alert('Đã sao chép link thành công!');
            });
        </script>
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
        <title>Đăng Nhập Tra Cứu - Zalo Affiliate</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-[#FAF8F5] text-slate-800 min-h-screen flex flex-col items-center justify-center p-4">
        <div class="max-w-md w-full bg-white rounded-3xl shadow-xl p-8 border border-slate-100">
            <a href="/" class="text-xs text-slate-400 hover:text-slate-700 flex items-center gap-1 mb-6 transition">
                <i class="fa-solid fa-arrow-left"></i> Quay lại trang chủ
            </a>

            <div class="flex items-center gap-3 mb-2">
                <div class="w-10 h-10 rounded-2xl bg-red-500 flex items-center justify-center text-white font-bold text-xl shadow-md shadow-red-500/20">
                    <i class="fa-solid fa-key"></i>
                </div>
                <h2 class="text-xl font-bold text-slate-900">Đăng Nhập Tra Cứu</h2>
            </div>
            
            <p class="text-slate-500 text-xs mb-6">Nhập Mã theo dõi do Bot Zalo cấp (Ví dụ: <code class="text-red-500 bg-red-50 px-2 py-0.5 rounded font-bold">zalo_vandotcf</code>) để kiểm tra đơn hàng.</p>

            <form id="loginForm" class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Mã Theo Dõi Cá Nhân</label>
                    <input type="text" id="trackingCode" placeholder="zalo_..." required 
                           class="w-full bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3.5 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-red-400 transition text-sm">
                </div>
                
                <div id="errMsg" class="hidden text-red-500 text-xs bg-red-50 p-3 rounded-xl border border-red-100"></div>

                <button type="submit" class="w-full py-3.5 px-4 rounded-2xl bg-[#E85B46] hover:bg-[#d44a36] text-white font-medium transition shadow-lg shadow-red-500/20 flex items-center justify-center gap-2 text-sm">
                    <i class="fa-solid fa-magnifying-glass"></i> Xem Đơn Hàng & Hoa Hồng
                </button>
            </form>

            <div class="mt-6 pt-6 border-t border-slate-100 text-center text-xs text-slate-400">
                Chưa có mã? Vào nhóm Zalo gõ <code class="text-red-500 font-bold">\id</code> để nhận mã cá nhân.
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
    <body class="bg-[#FAF8F5] text-slate-800 min-h-screen p-4 md:p-8">
        <div class="max-w-4xl mx-auto">
            <div class="flex items-center justify-between mb-6 bg-white p-6 rounded-3xl border border-slate-100 shadow-sm">
                <div>
                    <h1 class="text-2xl font-bold text-slate-900">📋 Báo Cáo Đơn Hàng & Hoa Hồng</h1>
                    <p class="text-slate-500 text-xs mt-1">Mã theo dõi: <span id="userCode" class="text-red-500 font-mono font-bold bg-red-50 px-2 py-0.5 rounded"></span></p>
                </div>
                <div class="flex gap-2">
                    <a href="/" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs rounded-xl font-medium transition flex items-center gap-1">
                        <i class="fa-solid fa-house"></i> Trang chủ
                    </a>
                    <a href="/login" class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white text-xs rounded-xl font-medium transition flex items-center gap-1">
                        <i class="fa-solid fa-arrow-right-from-bracket"></i> Đổi Mã
                    </a>
                </div>
            </div>

            <div class="bg-white rounded-3xl border border-slate-100 overflow-hidden shadow-xl">
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm text-slate-600">
                        <thead class="bg-slate-50 text-xs uppercase text-slate-400 border-b border-slate-100">
                            <tr>
                                <th class="p-4">Mã Đơn</th>
                                <th class="p-4">Sản Phẩm</th>
                                <th class="p-4">Giá Trị</th>
                                <th class="p-4">Hoa Hồng</th>
                                <th class="p-4">Trạng Thái</th>
                            </tr>
                        </thead>
                        <tbody id="ordersTable" class="divide-y divide-slate-100">
                            <tr><td colspan="5" class="p-8 text-center text-slate-400">Đang tải dữ liệu đơn hàng...</td></tr>
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
                        <tr class="hover:bg-slate-50 transition">
                            <td class="p-4 font-mono text-xs text-slate-400">${o.order_id}</td>
                            <td class="p-4 font-medium text-slate-800">${o.product_name}</td>
                            <td class="p-4">${Number(o.price).toLocaleString()}đ</td>
                            <td class="p-4 text-emerald-600 font-bold">+${Number(o.commission).toLocaleString()}đ</td>
                            <td class="p-4">
                                <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${o.status === 'Thành công' ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' : 'bg-amber-50 text-amber-600 border border-amber-200'}">
                                    ${o.status}
                                </span>
                            </td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = `<tr><td colspan="5" class="p-8 text-center text-slate-400">Chưa có đơn hàng nào phát sinh cho ID này trong 30 ngày qua.</td></tr>`;
                }
            }
            if (code) loadOrders();
        </script>
    </body>
    </html>
    """
    return render_template_string(html_orders)

# ==========================================
# 4. API BACKEND
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
