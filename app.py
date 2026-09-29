import os
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

DB_FILE = "church67.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY,
            believer_count INTEGER DEFAULT 0
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO stats (id, believer_count) VALUES (1, 67)")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS believers (
            user_id TEXT PRIMARY KEY,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# HTML 메인 페이지 서빙
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# 1. 신자 수 조회 API
@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT believer_count FROM stats WHERE id = 1")
    row = cursor.fetchone()
    count = row[0] if row else 67
    conn.close()
    return jsonify({"success": True, "believerCount": count})

# 2. 입교 신청 API (1인 1회 제한)
@app.route('/api/join', methods=['POST'])
def join():
    data = request.json or {}
    user_id = data.get('userId')
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    if not user_id:
        return jsonify({"success": False, "message": "유효하지 않은 사용자 ID입니다."}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM believers WHERE user_id = ? OR ip_address = ?", (user_id, client_ip))
    if cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "이미 67교 신자로 등록되어 있습니다! (1인 1회 제한)"}), 400

    cursor.execute("INSERT INTO believers (user_id, ip_address) VALUES (?, ?)", (user_id, client_ip))
    cursor.execute("UPDATE stats SET believer_count = believer_count + 1 WHERE id = 1")
    cursor.execute("SELECT believer_count FROM stats WHERE id = 1")
    new_count = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "성공적으로 67교에 입교하셨습니다!", "believerCount": new_count})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
