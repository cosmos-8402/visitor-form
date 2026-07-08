from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

def get_sheet():
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json)

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key("1B0YR6_clv6WfNdzubSTv4VJ7kVrjvdPrEJX6OSGhwhg").sheet1
    return sheet

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")
def health():
    return "OK", 200

@app.route("/admin")
def admin():
    return render_template("admin.html")

# ① 受付QR（入口QR） SVG Path 方式
@app.route("/reception_qr")
def reception_qr():
    url = "https://visitor-form-1.onrender.com"

    # SVG Path 方式（Render で最も安定）
    factory = qrcode.image.svg.SvgPathImage
    img = qrcode.make(url, image_factory=factory)

    buffer = BytesIO()
    img.save(buffer)
    qr_svg = buffer.getvalue().decode()

    return render_template("reception.html", qr_svg=qr_svg)

# ② 入力フォーム（visitor_id 発行）
@app.route('/api/visitor', methods=['POST'])
def visitor():
    data = request.json
    sheet = get_sheet()

    JST = pytz.timezone("Asia/Tokyo")
    now = datetime.now(JST)
    date_str = now.strftime("%Y/%m/%d")
    today_key = now.strftime("%Y%m%d")

    # 既存データ取得
    records = sheet.get_all_records()

    # 今日の visitor_id を抽出
    today_ids = [
        r["visitor_id"] for r in records
        if str(r["visitor_id"]).startswith(f"VIS-{today_key}")
    ]

    # 連番を決定
    if today_ids:
        last_num = max(int(t.split("-")[-1]) for t in today_ids)
        new_num = last_num + 1
    else:
        new_num = 1

    visitor_id = f"VIS-{today_key}-{new_num:03d}"

    # 時刻（JST）
    time_str = now.strftime("%H:%M")

    # シートに書き込み
    sheet.append_row([
        date_str,
        time_str,
        visitor_id,
        data.get("company"),
        data.get("name"),
        data.get("purpose")
    ])

    return jsonify({"visitor_id": visitor_id})

# ★③ 本人ID QR 表示ページ（PNG版・最速化）
@app.route("/visitor_qr/<visitor_id>")
def visitor_qr(visitor_id):

    # クエリパラメータ取得
    checkoutFlag = request.args.get("checkout")

    # visitor_id から ?checkout=done を除去（念のため）
    pure_id = visitor_id.split("?")[0]

    # QRコード生成
    qr = qrcode.QRCode(
        version=1,
        box_size=12,
        border=10
    )
    qr.add_data(pure_id)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#000000", back_color="#FFFFFF")

    buffer = BytesIO()
    img.save(buffer, format="PNG")

    qr_png = base64.b64encode(buffer.getvalue()).decode()

    # ★ checkoutFlag をテンプレートに渡す（これが最重要）
    return render_template(
        "visitor_qr.html",
        qr_png=qr_png,
        visitor_id=pure_id,
        checkoutFlag=checkoutFlag
    )

# ④ QRコード読み取り（退館用）
@app.route("/scan_checkout")
def scan_checkout():
    return render_template("scan_checkout.html")

@app.route("/checkout/<visitor_id>")
def checkout(visitor_id):
    sheet = get_sheet()

    # シート全体を取得
    records = sheet.get_all_records()

    # visitor_id の行番号を探す
    row_index = None
    for i, row in enumerate(records, start=2):  # 2行目からデータ
        if row.get("visitor_id") == visitor_id:
            row_index = i
            break

    if row_index is None:
        return f"ID {visitor_id} は見つかりませんでした。"

    # 退館時刻を記録（JST）
    JST = pytz.timezone("Asia/Tokyo")
    now = datetime.now(JST).strftime("%H:%M")
    sheet.update_cell(row_index, 7, now)  # G列に退館時刻を記録

    # ★ここでスマホ側へ「退館完了」を伝える
    return redirect(f"/visitor_qr/{visitor_id}?checkout=done")
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

   
