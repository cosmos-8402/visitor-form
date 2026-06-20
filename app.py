from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Render Flask connection successful!'

if __name__ == '__main__':
    app.run()
 
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import request, jsonify

def get_sheet():
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json)

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # ★センターのスプレッドシートID
    sheet = client.open_by_key("1B0YR6_clv6WfNdzubSTv4VJ7kVrjvdPrEJX6OSGhwhg").sheet1
    return sheet

@app.route('/api/visitor', methods=['POST'])
def visitor():
    data = request.json
    sheet = get_sheet()

    sheet.append_row([
        data.get("name"),
        data.get("company"),
        data.get("purpose"),
        data.get("time")
    ])

    return jsonify({"status": "success"})
