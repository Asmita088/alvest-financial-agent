from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from pathlib import Path
from AI_Agent_Model import predict_stock

app = Flask(__name__)
CORS(app)

DB_PATH = Path.cwd() / "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        email TEXT,
        password TEXT
    )''')
    conn.commit()
    conn.close()

def connect_db():
    return sqlite3.connect(DB_PATH)

init_db()

@app.route('/')
def home():
    return jsonify({"message": "Welcome to AIvest API"}), 200

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all([username, email, password]):
        return jsonify({"error": "All fields required"}), 400

    conn = connect_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?)", (username, email, password))
        conn.commit()
        return jsonify({"message": "User registered"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "User exists"}), 400
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE username=? AND password=?",
              (username, password))
    user = c.fetchone()
    conn.close()

    if user:
        return jsonify({"message": f"Welcome {username}"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/predict', methods=['GET'])
def predict():
    symbol = request.args.get('symbol', 'INFY.NS').upper()
    result = predict_stock(symbol, epochs=3)
    if not result:
        return jsonify({"error": "Stock data not available"}), 400

    score, latest, next_day, _ = result
    change_pct = ((next_day - latest) / (latest + 1e-9)) * 100

    if change_pct > 0.6:
        signal = "STRONG BUY 📈"
    elif change_pct > 0.1:
        signal = "BUY 📗"
    elif change_pct < -0.6:
        signal = "STRONG SELL 📉"
    elif change_pct < -0.1:
        signal = "SELL 📕"
    else:
        signal = "NEUTRAL ⚪"

    return jsonify({
        "stock": symbol,
        "current_price": f"₹{latest:.2f}",
        "predicted_next_day": f"₹{next_day:.2f}",
        "change_percentage": f"{change_pct:.2f}%",
        "confidence": f"{score*100:.2f}%",
        "signal": signal
    }), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
