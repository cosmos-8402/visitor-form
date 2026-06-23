from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import qrcode
import base64
from io import BytesIO
import os

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
@app.route("/register")
def register():
    return render_template("index.html")

# ③ 来訪者情報の受信API（ExcelはRenderで使えないので一時停止）
@app.route("/api/visitor", methods=["POST"])
def visitor():
    data = request.get_json()

    # Excel 書き込みは Render では不可のためコメントアウト
    # wb = openpyxl.load_workbook(r"C:\temp\パイトン\VisitorMaster.xlsx")
    # ws = wb.active

    now = datetime.now()
    visitor_id = f"TEST-{now.strftime('%Y%m%d-%H%M%S')}"

    return jsonify({"visitor_id": visitor_id})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port) 
