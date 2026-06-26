from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import qrcode
import base64
from io import BytesIO
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_sheet():
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json)

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # ★センターのスプレッドシートIDを入れる
    sheet = client.open_by_key("1B0YR6_clv6WfNdzubSTv4VJ7kVrjvdPrEJX6OSGhwhg").sheet1
    return sheet

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return render_template("index.html")

# ① 受付QR（入口QR）
@app.route("/reception_qr")
def reception_qr():
    url = "https://cosmos-8402.github.io/visitor-form/"

    qr = qrcode.make(url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render_template("reception.html", qr_base64=qr_base64)

# ② 入力フォーム
@app.route('/api/visitor', methods=['POST'])
def visitor():
    data = request.json
    sheet = get_sheet()

    now = datetime.now()
    date_str = now.strftime("%Y/%m/%d")
    time_str = now.strftime("%H:%M")
    visitor_id = f"VIS-{now.strftime('%Y%m%d-%H%M%S')}"

    sheet.append_row([
        date_str,
        time_str,
        visitor_id,
        data.get("company"),
        data.get("name"),
        data.get("purpose")
    ])

    return jsonify({"visitor_id": visitor_id})

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)  
