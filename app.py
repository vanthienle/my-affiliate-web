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
# 1. TRANG CHỦ (GIAO DIỆN MỚI - CÓ HÌNH NỀN)
# ==========================================

@app.route('/', methods=['GET'])
def index():
    html_home = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hệ Thống Chuyển Đổi Link Tự Động</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="text-slate-800 font-sans min-h-screen flex flex-col justify-between relative overflow-x-hidden">
        
        <!-- Ảnh nền & Lớp làm mờ 80% -->
        <div class="fixed inset-0 -z-20 bg-[url('https://i.postimg.cc/SRsvTY7D/pexels-steve-29404570.jpg')] bg-cover bg-center bg-no-repeat"></div>
        <div class="fixed inset-0 -z-10 bg-white/50 backdrop-blur-md"></div>

        <!-- HEADER / NAVIGATION -->
        <header class="max-w-6xl w-full mx-auto px-4 py-6 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <img src="https://i.postimg.cc/zfvsVWKV/Screenshot-2026-09-06-at-23-56-50.png" alt="Bot Shopping Logo" class="w-11 h-11 object-cover rounded-xl shadow-sm">
                <div class="hidden sm:block">
                    <div class="font-bold text-lg text-slate-800 tracking-tight leading-none mb-1">bot-shopping</div>
                    <div class="text-xs text-slate-600 font-medium leading-none">made by tay ngang gõ phím</div>
                </div>
            </div>

            <nav class="hidden md:flex items-center gap-2 bg-white/80 backdrop-blur border border-slate-200 rounded-full px-4 py-2 shadow-sm">
                <a href="/" class="px-4 py-2 rounded-full bg-blue-50 text-[#0068FF] font-semibold text-sm flex items-center gap-2">
                    <i class="fa-solid fa-house text-xs"></i> Trang chủ
                </a>
                <a href="/login" class="px-4 py-2 rounded-full hover:bg-slate-100 text-slate-700 font-medium text-sm transition flex items-center gap-2">
                    <i class="fa-solid fa-magnifying-glass text-xs"></i> Tra cứu đơn hàng
                </a>
            </nav>

            <div class="flex gap-2">
                <a href="https://zalo.me/g/gzjkxxocyzaaacu81hp6" target="_blank" class="px-4 py-2.5 rounded-full bg-[#0068FF] hover:bg-blue-600 text-white font-medium text-sm shadow-md transition flex items-center gap-2">
                    <i class="fa-solid fa-users text-xs"></i> <span class="hidden sm:inline">Vào nhóm Zalo</span>
                </a>
                <a href="/login" class="px-4 py-2.5 rounded-full bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-medium text-sm shadow-sm transition flex items-center gap-2">
                    <i class="fa-solid fa-right-to-bracket text-xs"></i> Đăng nhập
                </a>
            </div>
        </header>

        <!-- MAIN HERO CONTENT -->
        <main class="max-w-4xl mx-auto px-4 py-16 text-center flex-1 flex flex-col items-center justify-center">
            
            <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white border border-blue-100 text-[#0068FF] text-xs font-semibold mb-6 shadow-sm">
                <span class="w-2 h-2 rounded-full bg-[#0068FF] animate-pulse"></span> Công cụ tối ưu doanh thu Affiliate
            </div>

            <h1 class="text-4xl md:text-6xl font-extrabold text-slate-900 mb-5 tracking-tight leading-tight">
                Chuyển đổi link mua sắm <br/>
                <span class="text-[#0068FF] block mt-2 drop-shadow-sm">Tự động & Nhanh chóng</span>
            </h1>

            <p class="text-slate-700 font-medium text-base md:text-lg mb-10 max-w-xl mx-auto">
                Tạo link rút gọn và theo dõi hoa hồng từ các nền tảng thương mại điện tử hàng đầu trực tiếp trên hệ thống của chúng tôi.
            </p>

            <!-- KHUNG DÁN LINK CONVERT TRỰC TIẾP -->
            <div class="w-full bg-white/95 backdrop-blur-xl rounded-[2rem] p-5 md:p-8 shadow-2xl shadow-blue-900/10 border border-white/50 text-left relative overflow-hidden">
                
                <!-- Bảng các sàn hỗ trợ -->
                <div class="flex items-center gap-6 mb-5 px-1">
                    <span class="flex items-center gap-2 text-sm font-semibold text-orange-600 bg-orange-50 px-3 py-1.5 rounded-lg border border-orange-100">
                        <i class="fa-solid fa-bag-shopping"></i> Shopee
                    </span>
                    <span class="flex items-center gap-2 text-sm font-semibold text-slate-900 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">
                        <i class="fa-brands fa-tiktok"></i> TikTok
                    </span>
                    <span class="flex items-center gap-2 text-sm font-semibold text-blue-600 bg-blue-50 px-3 py-1.5 rounded-lg border border-blue-100">
                        <i class="fa-solid fa-layer-group"></i> Lazada
                    </span>
                </div>

                <!-- Input Box Group -->
                <div class="flex flex-col md:flex-row gap-3">
                    <button type="button" id="pasteBtn" class="px-5 py-3.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-2xl font-semibold text-sm transition flex items-center justify-center gap-2 whitespace-nowrap">
                        <i class="fa-solid fa-paste"></i> Dán link
                    </button>
                    
                    <div class="flex-1 relative">
                        <input type="text" id="rawUrl" placeholder="Nhập link sản phẩm cần chuyển đổi..." 
                               class="w-full bg-slate-50 border border-slate-200 focus:border-[#0068FF] focus:bg-white focus:ring-4 focus:ring-blue-500/10 rounded-2xl px-5 py-3.5 text-slate-800 placeholder-slate-400 focus:outline-none transition text-sm font-medium">
                    </div>

                    <button type="button" id="convertBtn" class="px-8 py-3.5 bg-[#0068FF] hover:bg-blue-700 text-white font-bold rounded-2xl transition shadow-lg shadow-blue-500/30 text-sm flex items-center justify-center gap-2 whitespace-nowrap">
                        <i class="fa-solid fa-wand-magic-sparkles"></i> Tạo Link
                    </button>
                </div>

                <!-- KHU VỰC HIỆN KẾT QUẢ LINK AFTER CONVERT -->
                <div id="resultBox" class="hidden mt-6 pt-6 border-t border-slate-100">
                    <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">LINK CHIA SẺ CỦA BẠN:</label>
                    <div class="flex gap-2">
                        <input type="text" id="outLink" readonly class="flex-1 bg-emerald-50 border border-emerald-200 text-emerald-700 font-bold rounded-xl px-4 py-3 text-sm focus:outline-none">
                        <!-- NÚT MUA NGAY -->
                        <a href="#" id="buyBtn" target="_blank" class="px-8 py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-bold rounded-xl text-sm transition flex items-center justify-center gap-2 whitespace-nowrap shadow-md">
                            <i class="fa-solid fa-cart-shopping"></i> Mua ngay
                        </a>
                    </div>
                </div>
            </div>

            <!-- Nút Action Phụ -->
            <div class="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
                <a href="https://zalo.me/g/gzjkxxocyzaaacu81hp6" target="_blank" class="px-8 py-3.5 bg-white border-2 border-[#0068FF] text-[#0068FF] hover:bg-blue-50 font-bold rounded-full transition shadow-sm text-sm inline-flex items-center justify-center gap-2">
                    <i class="fa-solid fa-users"></i> Tham gia cộng đồng Zalo
                </a>
                <a href="/login" class="px-8 py-3.5 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-full shadow-lg transition text-sm inline-flex items-center justify-center gap-2">
                    <i class="fa-solid fa-chart-pie"></i> Xem báo cáo hoa hồng
                </a>
            </div>
        </main>

        <footer class="py-6 text-center text-xs font-semibold text-slate-600 border-t border-white/40 bg-white/30 backdrop-blur-sm">
            © 2026 bot-shopping. Quản lý bởi Bot Tự Động.
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
                    alert('Vui lòng nhập link sản phẩm cần chuyển đổi!');
                    return;
                }

                const res = await fetch('/api/convert', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url })
                });

                const result = await res.json();
                if (result.success) {
                    // Gán link vào ô input hiển thị
                    document.getElementById('outLink').value = result.data.short_link;
                    // Gắn trực tiếp link vào href của nút "Mua ngay"
                    document.getElementById('buyBtn').href = result.data.short_link;
                    
                    document.getElementById('resultBox').classList.remove('hidden');
                } else {
                    alert('Lỗi chuyển đổi link!');
                }
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
        <title>Đăng Nhập Quản Lý - bot-shopping</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="text-slate-800 min-h-screen flex flex-col items-center justify-center p-4 relative">
        
        <!-- Ảnh nền & Lớp làm mờ 80% -->
        <div class="fixed inset-0 -z-20 bg-[url('https://i.postimg.cc/SRsvTY7D/pexels-steve-29404570.jpg')] bg-cover bg-center bg-no-repeat"></div>
        <div class="fixed inset-0 -z-10 bg-white/80 backdrop-blur-md"></div>

        <div class="max-w-md w-full bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl p-8 border border-white/50">
            <a href="/" class="text-xs font-semibold text-slate-500 hover:text-slate-800 flex items-center gap-1 mb-6 transition">
                <i class="fa-solid fa-arrow-left"></i> Về trang chủ
            </a>

            <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 rounded-xl bg-[#0068FF] flex items-center justify-center text-white font-bold text-lg shadow-md shadow-blue-500/20">
                    <i class="fa-solid fa-shield-halved"></i>
                </div>
                <h2 class="text-2xl font-extrabold text-slate-900">Tra Cứu Đơn Hàng</h2>
            </div>
            
            <p class="text-slate-600 font-medium text-sm mb-6">Nhập Mã theo dõi được Bot cấp trong nhóm Zalo (Vd: <code class="text-[#0068FF] bg-blue-50 px-2 py-0.5 rounded font-bold">zalo_uid</code>).</p>

            <form id="loginForm" class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Mã Tra Cứu (ID)</label>
                    <input type="text" id="trackingCode" placeholder="Nhập mã của bạn..." required 
                           class="w-full bg-slate-50 border border-slate-200 rounded-2xl px-5 py-4 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-[#0068FF] focus:ring-4 focus:ring-blue-500/10 transition text-sm font-bold">
                </div>
                
                <div id="errMsg" class="hidden text-red-600 text-xs font-semibold bg-red-50 p-3 rounded-xl border border-red-100"></div>

                <button type="submit" class="w-full py-4 px-4 rounded-2xl bg-[#0068FF] hover:bg-blue-700 text-white font-bold transition shadow-lg shadow-blue-500/30 flex items-center justify-center gap-2 text-sm">
                    <i class="fa-solid fa-magnifying-glass"></i> Kiểm Tra Hoa Hồng
                </button>
            </form>

            <div class="mt-6 pt-6 border-t border-slate-100 text-center text-xs font-medium text-slate-500">
                Chưa có mã? Gõ <code class="text-[#0068FF] font-bold">\id</code> trong nhóm Zalo để nhận.
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
        <title>Báo Cáo Hoa Hồng - bot-shopping</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="text-slate-800 min-h-screen p-4 md:p-8 relative">
        
        <!-- Ảnh nền & Lớp làm mờ 80% -->
        <div class="fixed inset-0 -z-20 bg-[url('https://i.postimg.cc/SRsvTY7D/pexels-steve-29404570.jpg')] bg-cover bg-center bg-no-repeat"></div>
        <div class="fixed inset-0 -z-10 bg-white/80 backdrop-blur-md"></div>

        <div class="max-w-4xl mx-auto relative z-10">
            <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6 bg-white/95 backdrop-blur-xl p-6 rounded-3xl border border-white/50 shadow-xl shadow-slate-200/20">
                <div>
                    <h1 class="text-2xl font-extrabold text-slate-900">Báo Cáo Hoa Hồng</h1>
                    <p class="text-slate-600 font-medium text-sm mt-1">ID Đang truy cập: <span id="userCode" class="text-[#0068FF] font-mono font-bold bg-blue-50 px-2 py-0.5 rounded border border-blue-100"></span></p>
                </div>
                <div class="flex gap-2 w-full sm:w-auto">
                    <a href="/" class="flex-1 sm:flex-none justify-center px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm rounded-xl font-bold transition flex items-center gap-2">
                        <i class="fa-solid fa-house"></i> Home
                    </a>
                    <a href="/login" class="flex-1 sm:flex-none justify-center px-5 py-2.5 bg-[#0068FF] hover:bg-blue-600 text-white text-sm rounded-xl font-bold transition flex items-center gap-2 shadow-md">
                        <i class="fa-solid fa-right-from-bracket"></i> Đăng xuất
                    </a>
                </div>
            </div>

            <div class="bg-white/95 backdrop-blur-xl rounded-3xl border border-white/50 overflow-hidden shadow-2xl shadow-slate-200/40">
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm text-slate-700 font-medium">
                        <thead class="bg-slate-50/80 text-xs uppercase text-slate-500 border-b border-slate-100 font-bold">
                            <tr>
                                <th class="p-5">Mã Đơn</th>
                                <th class="p-5">Sản Phẩm</th>
                                <th class="p-5">Giá Trị</th>
                                <th class="p-5">Hoa Hồng</th>
                                <th class="p-5">Trạng Thái</th>
                            </tr>
                        </thead>
                        <tbody id="ordersTable" class="divide-y divide-slate-100">
                            <tr><td colspan="5" class="p-8 text-center text-slate-500 font-semibold">Đang tải dữ liệu...</td></tr>
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
                            <td class="p-5 font-mono text-xs text-slate-500">${o.order_id}</td>
                            <td class="p-5 font-bold text-slate-800 line-clamp-2">${o.product_name}</td>
                            <td class="p-5">${Number(o.price).toLocaleString()}đ</td>
                            <td class="p-5 text-emerald-600 font-extrabold">+${Number(o.commission).toLocaleString()}đ</td>
                            <td class="p-5">
                                <span class="px-3 py-1.5 rounded-lg text-xs font-bold ${o.status === 'Thành công' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'}">
                                    ${o.status}
                                </span>
                            </td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = `<tr><td colspan="5" class="p-10 text-center text-slate-600 bg-slate-50/50">Không tìm thấy đơn hàng nào trong 30 ngày qua cho mã <b class="text-[#0068FF]">${code}</b></td></tr>`;
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
