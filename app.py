import os
import string
import random
import sqlite3
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect, session
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "zalo_affiliate_secret_key_pro"
CORS(app, supports_credentials=True)

ACCESSTRADE_TOKEN = "4XeA52l7Vi-YlHdi7E1JBh43qeIX0iJ6"
BASE_DOMAIN = "https://bot-shopping.onrender.com"
DB_PATH = "links.db"

def init_db():
    """Khởi tạo SQLite Database lưu trữ mã rút gọn"""
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
    """Tạo ngẫu nhiên mã chuỗi rút gọn 6 ký tự"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "running", "service": "Zalo Affiliate Web Service"})

@app.route('/api/convert', methods=['POST'])
def convert_url():
    """API rút gọn link dạng /s/<code>"""
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
    """Điều hướng link rút gọn sang link sản phẩm/affiliate gốc"""
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
    """API Đăng nhập bằng Mã theo dõi do Bot Zalo cấp"""
    data = request.json or {}
    tracking_code = data.get('tracking_code', '').strip().lower()

    if not tracking_code:
        return jsonify({"success": False, "message": "Vui lòng nhập Mã theo dõi"}), 400

    session['user_utm'] = tracking_code
    return jsonify({
        "success": True,
        "message": "Đăng nhập thành công",
        "tracking_code": tracking_code,
        "redirect": "/app/orders"
    })

@app.route('/api/user-orders', methods=['GET'])
def get_user_orders():
    """API Lấy danh sách đơn hàng tra soát theo Mã theo dõi"""
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
