from flask import Flask, render_template, request, jsonify
import re
import requests
import unicodedata

app = Flask(__name__)

ACCESSTRADE_TOKEN = "4XeA52l7Vi-YlHdi7E1JBh43qeIX0iJ6"
CAMPAIGNS = {
    "Shopee": "4751584435713464237",
    "TikTok": "6648523843406889655"
}

def strip_accents(text):
    if not text: return ""
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.replace('đ', 'd').replace('Đ', 'D').lower()

def convert_and_estimate(origin_url):
    # 1. Giải mã & Làm sạch URL
    try:
        resp = requests.get(origin_url, headers={'User-Agent': 'Mozilla/5.0'}, allow_redirects=True, timeout=5)
        full_url = resp.url if resp.url else origin_url
    except:
        full_url = origin_url

    platform = "Shopee" if any(x in full_url.lower() for x in ["shopee", "shp"]) else ("TikTok" if "tiktok" in full_url.lower() else "Lazada")
    campaign_id = CAMPAIGNS.get(platform)
    
    target_url = full_url.split('?')[0]
    if platform == "Shopee":
        m = re.search(r'i\.(\d+)\.(\d+)', full_url) or re.search(r'product/(\d+)/(\d+)', full_url)
        if m: target_url = f"https://shopee.vn/product/{m.group(1)}/{m.group(2)}"
    elif platform == "TikTok":
        m = re.search(r'product/(\d+)', full_url)
        if m: target_url = f"https://shop.tiktok.com/view/product/{m.group(1)}"

    # 2. Tạo Link Affiliate
    aff_link = None
    if campaign_id:
        api_url = "https://api.accesstrade.vn/v1/product_link/create"
        payload = {"campaign_id": campaign_id, "urls": [target_url], "utm_source": "web_site"}
        headers = {"Authorization": f"Token {ACCESSTRADE_TOKEN}", "Content-Type": "application/json"}
        try:
            r = requests.post(api_url, json=payload, headers=headers, timeout=5)
            if r.status_code == 200:
                data = r.json().get("data", {}).get("success_link", [])
                if data: aff_link = data[0].get("short_link") or data[0].get("aff_link")
        except: pass

    # 3. Bóc tách thông tin sản phẩm & giá
    title, price = "Sản phẩm ưu đãi", 0
    if platform == "Shopee":
        m = re.search(r'product/(\d+)/(\d+)', target_url)
        if m:
            try:
                res = requests.get(f"https://shopee.vn/api/v4/item/get?itemid={m.group(2)}&shopid={m.group(1)}", headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                if res.status_code == 200:
                    data = res.json().get("data", {}) or {}
                    price = float(data.get("price") or data.get("price_min") or 0) / 100000.0
                    title = data.get("name", title)
            except: pass

    return {
        "platform": platform,
        "title": title,
        "price": price,
        "aff_link": aff_link or target_url
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/convert', methods=['POST'])
def api_convert():
    data = request.json or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"success": False, "message": "Vui lòng nhập đường dẫn sản phẩm"}), 400
    
    result = convert_and_estimate(url)
    return jsonify({"success": True, "data": result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
